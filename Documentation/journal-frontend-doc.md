# Personal Journal AI - Frontend Implementation Guide

## Overview
A minimalist desktop journal application with a persistent left sidebar (Notion-style), voice-first entry creation, and intelligent pattern recognition.

## Design Philosophy
- Always-visible left sidebar for quick navigation
- Plus button for instant entry creation
- Voice-first with text fallback
- Pattern insights appear after 30 entries
- Clean, focused interface with minimal distractions

## Tech Stack
- **UI Framework**: React with TypeScript
- **Component Library**: shadcn/ui
- **Styling**: Tailwind CSS
- **Desktop Wrapper**: Electron
- **Icons**: Lucide React
- **Voice**: Web Speech API (integrates with your existing transcriber)

## Color Scheme
```css
/* Base Grayscale */
--background: 250 250 250      /* Soft white #FAFAFA */
--foreground: 23 23 23         /* Rich black #171717 */
--card: 255 255 255            /* Pure white #FFFFFF */
--muted: 245 245 245           /* Light gray #F5F5F5 */
--muted-foreground: 115 115 115 /* Medium gray #737373 */
--border: 229 229 229          /* Light border #E5E5E5 */

/* Accent Colors */
--primary: 99 102 241          /* Indigo #6366F1 */
--secondary: 244 114 182       /* Pink #F472B6 */
--accent: 251 146 60           /* Orange #FB923C */
--success: 34 197 94           /* Green #22C55E */
```

## Application Layout

### Main Layout with Persistent Sidebar
```jsx
// app/layout.tsx
export default function RootLayout({ children }) {
  const [entries, setEntries] = useState([])
  const [showPatterns, setShowPatterns] = useState(false)

  useEffect(() => {
    // Check if user has 30+ entries
    if (entries.length >= 30) {
      setShowPatterns(true)
    }
  }, [entries])

  return (
    <div className="flex h-screen bg-background">
      {/* Left Sidebar - Always Visible */}
      <aside className="w-64 border-r bg-card flex flex-col">
        {/* Logo/Title */}
        <div className="p-4 border-b">
          <h1 className="font-semibold text-lg">Personal Journal</h1>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          <div className="space-y-2">
            {/* New Entry Button */}
            <Link to="/new">
              <Button className="w-full justify-start" variant="ghost">
                <Plus className="mr-3 h-5 w-5" />
                New Entry
              </Button>
            </Link>

            {/* View Entries */}
            <Link to="/entries">
              <Button className="w-full justify-start" variant="ghost">
                <FileText className="mr-3 h-5 w-5" />
                View Entries
              </Button>
            </Link>

            {/* Talk to Diary */}
            <Link to="/talk">
              <Button className="w-full justify-start" variant="ghost">
                <MessageSquare className="mr-3 h-5 w-5" />
                Talk to Your Diary
              </Button>
            </Link>

            {/* Pattern Insights - Shows after 30 entries */}
            {showPatterns && (
              <Link to="/patterns">
                <Button className="w-full justify-start" variant="ghost">
                  <Diamond className="mr-3 h-5 w-5 text-primary" />
                  Pattern Insights
                </Button>
              </Link>
            )}

            {/* Memories */}
            <Link to="/memories">
              <Button className="w-full justify-start" variant="ghost">
                <Calendar className="mr-3 h-5 w-5" />
                Memories
              </Button>
            </Link>

            {/* Settings */}
            <Link to="/settings">
              <Button className="w-full justify-start" variant="ghost">
                <Settings className="mr-3 h-5 w-5" />
                Settings
              </Button>
            </Link>
          </div>
        </nav>

        {/* Bottom Section - Streak */}
        <div className="p-4 border-t">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Daily Streak</span>
            <Badge variant="secondary" className="bg-orange-100 text-orange-700">
              <Flame className="mr-1 h-3 w-3" />
              5 days
            </Badge>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>

      {/* Floating Plus Button */}
      <Link to="/new">
        <Button
          size="lg"
          className="fixed bottom-8 right-8 h-14 w-14 rounded-full shadow-lg bg-primary hover:bg-primary/90"
        >
          <Plus className="h-6 w-6" />
        </Button>
      </Link>
    </div>
  )
}
```

### New Entry Page with Whisper Integration and State Management
```jsx
// pages/NewEntry.tsx
import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Mic, MicOff, Loader2, Keyboard, CheckCircle } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
import { motion, AnimatePresence } from 'framer-motion'

// Recording states
const RecordingState = {
  IDLE: 'idle',
  RECORDING: 'recording',
  PROCESSING: 'processing',
  TRANSCRIBING: 'transcribing',
  ENHANCING: 'enhancing',
  SUCCESS: 'success'
}

export function NewEntryPage() {
  const [text, setText] = useState('')
  const [recordingState, setRecordingState] = useState(RecordingState.IDLE)
  const [isProcessing, setIsProcessing] = useState(false)
  const [createdEntries, setCreatedEntries] = useState(null)
  const [currentHotkey, setCurrentHotkey] = useState('F8')
  const [isHotkeyPressed, setIsHotkeyPressed] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    // Get current hotkey from settings
    loadHotkey()
    
    // Listen for transcription completion
    window.electron.transcription.onComplete((transcribedText) => {
      setText(prevText => prevText + (prevText ? ' ' : '') + transcribedText)
      setRecordingState(RecordingState.IDLE)
    })

    // Listen for state changes from Whisper service
    window.electron.transcription.onStateChange((state) => {
      setRecordingState(state)
    })

    // Listen for global hotkey press
    window.electron.transcription.onHotkeyPress(() => {
      if (!isHotkeyPressed) {
        startRecording()
        setIsHotkeyPressed(true)
      }
    })

    // Listen for hotkey release
    const handleKeyUp = (e) => {
      if (isHotkeyPressed && !e.repeat) {
        stopRecording()
        setIsHotkeyPressed(false)
      }
    }
    
    window.addEventListener('keyup', handleKeyUp)
    
    return () => {
      window.removeEventListener('keyup', handleKeyUp)
    }
  }, [isHotkeyPressed])

  const loadHotkey = async () => {
    const hotkey = await window.electron.hotkey.getCurrent()
    setCurrentHotkey(hotkey)
  }

  const startRecording = () => {
    if (recordingState === RecordingState.IDLE) {
      setRecordingState(RecordingState.RECORDING)
      window.electron.transcription.start()
    }
  }

  const stopRecording = () => {
    if (recordingState === RecordingState.RECORDING) {
      setRecordingState(RecordingState.PROCESSING)
      window.electron.transcription.stop()
    }
  }

  const createEntries = async () => {
    if (!text.trim()) {
      toast({
        title: "No content",
        description: "Please record or type something first",
        variant: "destructive"
      })
      return
    }

    setIsProcessing(true)
    setRecordingState(RecordingState.ENHANCING)
    
    try {
      // Create entry with all three modes
      const response = await api.createEntry(text, 'all')
      
      setCreatedEntries({
        raw: response.data.raw,
        enhanced: response.data.enhanced,
        structured: response.data.structured
      })
      
      // Show success state briefly
      setRecordingState(RecordingState.SUCCESS)
      setTimeout(() => setRecordingState(RecordingState.IDLE), 2000)
      
      // Success toast with checkmarks
      toast({
        title: "✓ Entries created!",
        description: (
          <div className="space-y-1 mt-2">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-3 w-3 text-green-500" />
              <span className="text-sm">Raw transcription saved</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-3 w-3 text-green-500" />
              <span className="text-sm">Enhanced style created</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-3 w-3 text-green-500" />
              <span className="text-sm">Structured summary generated</span>
            </div>
          </div>
        ),
      })
      
      // Clear for next entry
      setText('')
      
      // Check for milestones
      checkMilestones()
      
    } catch (error) {
      setRecordingState(RecordingState.IDLE)
      toast({
        title: "Error",
        description: "Failed to create entries",
        variant: "destructive"
      })
    } finally {
      setIsProcessing(false)
    }
  }

  const checkMilestones = async () => {
    const milestones = await api.checkMilestones()
    milestones.data.forEach(milestone => {
      if (milestone.type === 'pattern_unlock') {
        showPatternUnlockCelebration()
      } else if (milestone.type === 'coffee') {
        showCoffeePopup(milestone)
      }
    })
  }

  const getStateMessage = () => {
    switch (recordingState) {
      case RecordingState.RECORDING:
        return `Recording... Release ${currentHotkey} to stop`
      case RecordingState.PROCESSING:
        return "Processing audio..."
      case RecordingState.TRANSCRIBING:
        return "Converting speech to text..."
      case RecordingState.ENHANCING:
        return "Creating enhanced versions..."
      case RecordingState.SUCCESS:
        return "Entries created!"
      default:
        return `Hold ${currentHotkey} to record`
    }
  }

  const getStateIcon = () => {
    switch (recordingState) {
      case RecordingState.RECORDING:
        return <div className="h-2 w-2 bg-red-500 rounded-full animate-pulse" />
      case RecordingState.PROCESSING:
      case RecordingState.TRANSCRIBING:
      case RecordingState.ENHANCING:
        return <Loader2 className="h-4 w-4 animate-spin" />
      case RecordingState.SUCCESS:
        return <CheckCircle className="h-4 w-4 text-green-500" />
      default:
        return null
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-8">
      <h2 className="text-2xl font-bold mb-6">New Entry</h2>

      <Card className="p-6">
        <div className="relative">
          {/* Text Input Area */}
          <Textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={`Start typing or hold ${currentHotkey} to speak...`}
            className="min-h-[300px] resize-none pr-16 text-lg"
          />

          {/* Voice Recording Button & Hotkey Indicator */}
          <div className="absolute bottom-4 right-4 flex flex-col items-center gap-2">
            <Button
              size="icon"
              variant={recordingState === RecordingState.RECORDING ? "destructive" : "default"}
              className={recordingState === RecordingState.RECORDING ? 'animate-pulse' : ''}
              onMouseDown={startRecording}
              onMouseUp={stopRecording}
              onMouseLeave={stopRecording}
              title={`Hold to record (or hold ${currentHotkey})`}
              disabled={recordingState !== RecordingState.IDLE && recordingState !== RecordingState.RECORDING}
            >
              {recordingState === RecordingState.RECORDING ? (
                <MicOff className="h-5 w-5" />
              ) : (
                <Mic className="h-5 w-5" />
              )}
            </Button>
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Keyboard className="h-3 w-3" />
              <span>Hold {currentHotkey}</span>
            </div>
          </div>
        </div>

        {/* State Indicator */}
        <AnimatePresence>
          {recordingState !== RecordingState.IDLE && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mt-4 flex items-center gap-2 text-sm"
            >
              {getStateIcon()}
              <span className={recordingState === RecordingState.SUCCESS ? 'text-green-600' : 'text-primary'}>
                {getStateMessage()}
              </span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Create Entries Button */}
        <div className="mt-6 flex justify-end">
          <Button
            size="lg"
            onClick={createEntries}
            disabled={isProcessing || !text.trim() || recordingState !== RecordingState.IDLE}
          >
            {isProcessing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Create All Three Entries
          </Button>
        </div>
      </Card>

      {/* Preview Created Entries (same as before) */}
      {createdEntries && (
        <div className="mt-8 space-y-4">
          {/* ... existing preview code ... */}
        </div>
      )}
    </div>
  )
}
```

  const createEntries = async () => {
    if (!text.trim()) {
      toast({
        title: "No content",
        description: "Please record or type something first",
        variant: "destructive"
      })
      return
    }

    setIsProcessing(true)
    
    try {
      // Create entry with all three modes
      const response = await api.createEntry(text, 'all')
      
      setCreatedEntries({
        raw: response.data.raw,
        enhanced: response.data.enhanced,
        structured: response.data.structured
      })
      
      toast({
        title: "Entries created!",
        description: "Your thoughts have been saved in all three formats",
      })
      
      // Clear for next entry
      setText('')
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create entries",
        variant: "destructive"
      })
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-8">
      <h2 className="text-2xl font-bold mb-6">New Entry</h2>

      <Card className="p-6">
        <div className="relative">
          {/* Text Input Area */}
          <Textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Start typing or use your hotkey to speak..."
            className="min-h-[300px] resize-none pr-16 text-lg"
          />

          {/* Voice Recording Button */}
          <div className="absolute bottom-4 right-4 flex flex-col items-center gap-2">
            <Button
              size="icon"
              variant={isRecording ? "destructive" : "default"}
              className={isRecording && 'animate-pulse'}
              onClick={isRecording ? stopRecording : startRecording}
              title={`Voice input (or press ${currentHotkey})`}
            >
              {isRecording ? (
                <MicOff className="h-5 w-5" />
              ) : (
                <Mic className="h-5 w-5" />
              )}
            </Button>
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <Keyboard className="h-3 w-3" />
              {currentHotkey}
            </span>
          </div>
        </div>

        {/* Create Entries Button */}
        <div className="mt-6 flex justify-end">
          <Button
            size="lg"
            onClick={createEntries}
            disabled={isProcessing || !text.trim()}
          >
            {isProcessing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Create All Three Entries
          </Button>
        </div>
      </Card>

      {/* Preview Created Entries */}
      {createdEntries && (
        <div className="mt-8 space-y-4">
          <h3 className="text-lg font-semibold">Created Entries:</h3>
          
          <Card className="p-4 border-l-4 border-l-primary">
            <h4 className="font-medium mb-2">Raw Transcription</h4>
            <p className="text-sm text-muted-foreground">{createdEntries.raw}</p>
          </Card>
          
          <Card className="p-4 border-l-4 border-l-secondary">
            <h4 className="font-medium mb-2">Enhanced Style</h4>
            <p className="text-sm text-muted-foreground">{createdEntries.enhanced}</p>
          </Card>
          
          <Card className="p-4 border-l-4 border-l-accent">
            <h4 className="font-medium mb-2">Structured Summary</h4>
            <p className="text-sm text-muted-foreground">{createdEntries.structured}</p>
          </Card>
        </div>
      )}
    </div>
  )
}
```

### View Entries Page (Browse All Entries)
```jsx
// pages/ViewEntries.tsx
import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Calendar, Clock } from 'lucide-react'
import { format } from 'date-fns'

export function ViewEntriesPage() {
  const [entries, setEntries] = useState([])
  const [selectedMode, setSelectedMode] = useState('all')
  const [selectedEntry, setSelectedEntry] = useState(null)

  useEffect(() => {
    fetchEntries()
  }, [])

  const fetchEntries = async () => {
    const response = await api.getEntries()
    setEntries(response.data)
  }

  return (
    <div className="flex h-full">
      {/* Entry List - Left Side */}
      <div className="w-96 border-r overflow-auto bg-muted/20">
        <div className="p-4 border-b bg-background sticky top-0 z-10">
          <h2 className="text-xl font-bold mb-4">Your Entries</h2>
          
          {/* Mode Filter Tabs */}
          <Tabs value={selectedMode} onValueChange={setSelectedMode}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="all">All</TabsTrigger>
              <TabsTrigger value="raw">Raw</TabsTrigger>
              <TabsTrigger value="enhanced">Enhanced</TabsTrigger>
              <TabsTrigger value="structured">Structured</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        {/* Entry List */}
        <div className="p-4 space-y-3">
          {entries
            .filter(entry => selectedMode === 'all' || entry.mode === selectedMode)
            .map((entry) => (
              <Card
                key={entry.id}
                className={`p-4 cursor-pointer transition-all hover:shadow-md ${
                  selectedEntry?.id === entry.id ? 'ring-2 ring-primary' : ''
                }`}
                onClick={() => setSelectedEntry(entry)}
              >
                <div className="flex items-start justify-between mb-2">
                  <Badge variant="outline" className="text-xs">
                    {entry.mode}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {format(new Date(entry.timestamp), 'MMM d')}
                  </span>
                </div>
                <p className="text-sm line-clamp-3">
                  {entry.raw_text}
                </p>
                <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {format(new Date(entry.timestamp), 'h:mm a')}
                  </span>
                  <span>{entry.word_count} words</span>
                </div>
              </Card>
            ))}
        </div>
      </div>

      {/* Entry Detail - Right Side */}
      <div className="flex-1 overflow-auto">
        {selectedEntry ? (
          <div className="p-8 max-w-4xl mx-auto">
            <div className="mb-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-2xl font-bold">Entry Details</h3>
                <Badge>{selectedEntry.mode}</Badge>
              </div>
              <p className="text-muted-foreground">
                {format(new Date(selectedEntry.timestamp), 'EEEE, MMMM d, yyyy • h:mm a')}
              </p>
            </div>

            {/* Display all three versions */}
            <div className="space-y-6">
              <Card className="p-6">
                <h4 className="font-semibold mb-3 text-primary">Raw Transcription</h4>
                <p className="whitespace-pre-wrap">{selectedEntry.raw_text}</p>
              </Card>

              {selectedEntry.enhanced_text && (
                <Card className="p-6">
                  <h4 className="font-semibold mb-3 text-secondary">Enhanced Style</h4>
                  <p className="whitespace-pre-wrap">{selectedEntry.enhanced_text}</p>
                </Card>
              )}

              {selectedEntry.structured_summary && (
                <Card className="p-6">
                  <h4 className="font-semibold mb-3 text-accent">Structured Summary</h4>
                  <p className="whitespace-pre-wrap">{selectedEntry.structured_summary}</p>
                </Card>
              )}

              {/* Mood Tags */}
              {selectedEntry.mood_tags && (
                <div className="flex gap-2 flex-wrap">
                  {selectedEntry.mood_tags.map((tag, i) => (
                    <Badge key={i} variant="secondary">
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            Select an entry to view details
          </div>
        )}
      </div>
    </div>
  )
}
```

### Pattern Insights Page (Diamond Button - After 30 Entries)
```jsx
// pages/PatternInsights.tsx
import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Diamond, TrendingUp, Brain, Calendar } from 'lucide-react'

export function PatternInsightsPage() {
  const [patterns, setPatterns] = useState([])
  const [selectedPattern, setSelectedPattern] = useState(null)
  const [relatedEntries, setRelatedEntries] = useState([])

  useEffect(() => {
    fetchPatterns()
  }, [])

  const fetchPatterns = async () => {
    const response = await api.getPatterns()
    setPatterns(response.data)
  }

  const selectPattern = async (pattern) => {
    setSelectedPattern(pattern)
    // Fetch entries related to this pattern
    const entries = await api.getEntriesForPattern(pattern.id)
    setRelatedEntries(entries.data)
  }

  const patternIcons = {
    mood: Brain,
    temporal: Calendar,
    topic: TrendingUp
  }

  return (
    <div className="max-w-6xl mx-auto p-8">
      <div className="text-center mb-8">
        <Diamond className="h-12 w-12 text-primary mx-auto mb-4" />
        <h1 className="text-3xl font-bold mb-2">Pattern Insights</h1>
        <p className="text-muted-foreground">
          Discovered patterns from your {patterns.length > 0 ? patterns[0].total_entries : '30+'} journal entries
        </p>
      </div>

      {/* Pattern Bubbles */}
      <div className="flex flex-wrap gap-4 justify-center mb-12">
        {patterns.map((pattern) => {
          const Icon = patternIcons[pattern.pattern_type] || Diamond
          return (
            <Button
              key={pattern.id}
              variant={selectedPattern?.id === pattern.id ? "default" : "outline"}
              className="h-auto p-4 flex flex-col items-center gap-2 min-w-[150px]"
              onClick={() => selectPattern(pattern)}
            >
              <Icon className="h-6 w-6" />
              <span className="text-sm font-medium">{pattern.description}</span>
              <Badge variant="secondary" className="text-xs">
                {pattern.frequency} occurrences
              </Badge>
            </Button>
          )
        })}
      </div>

      {/* Selected Pattern Details */}
      {selectedPattern && (
        <div className="space-y-6">
          <Card className="p-6 bg-primary/5 border-primary/20">
            <h3 className="text-lg font-semibold mb-2">
              Pattern: {selectedPattern.description}
            </h3>
            <p className="text-muted-foreground">
              This pattern has appeared {selectedPattern.frequency} times 
              between {format(new Date(selectedPattern.first_seen), 'MMM d')} and {format(new Date(selectedPattern.last_seen), 'MMM d')}.
            </p>
          </Card>

          {/* Example Entries */}
          <div>
            <h4 className="font-semibold mb-4">Example Entries with This Pattern:</h4>
            <div className="space-y-3">
              {relatedEntries.slice(0, 3).map((entry) => (
                <Card key={entry.id} className="p-4">
                  <div className="flex justify-between items-start mb-2">
                    <Badge variant="outline" className="text-xs">
                      {format(new Date(entry.timestamp), 'MMM d, yyyy')}
                    </Badge>
                  </div>
                  <p className="text-sm line-clamp-3">{entry.raw_text}</p>
                  {/* Highlight the pattern in the text */}
                  <div className="mt-2">
                    <Badge className="text-xs" variant="secondary">
                      Pattern match
                    </Badge>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
```

### Home Page (Updated to Match Backend Modes)
```jsx
// pages/Home.tsx
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { FileText, Sparkles, LayoutList } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export function HomePage() {
  const navigate = useNavigate()
  
  const viewModes = [
    {
      icon: FileText,
      title: "Raw Transcription",
      description: "Your exact words, unfiltered and authentic",
      color: "text-primary",
      bgColor: "bg-primary/10",
      mode: "raw"
    },
    {
      icon: Sparkles,
      title: "Enhanced Style",
      description: "Improved grammar and tone while preserving your intent",
      color: "text-secondary",
      bgColor: "bg-secondary/10",
      mode: "enhanced"
    },
    {
      icon: LayoutList,
      title: "Structured Summary",
      description: "Organized into coherent themes and key points",
      color: "text-accent",
      bgColor: "bg-accent/10",
      mode: "structured"
    }
  ]

  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">Welcome to Your Journal</h1>
        <p className="text-muted-foreground text-lg">
          Express yourself in three different ways
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6 mb-12">
        {viewModes.map((mode) => (
          <Card 
            key={mode.mode}
            className="cursor-pointer transition-all hover:shadow-lg hover:-translate-y-1"
            onClick={() => navigate('/entries')}
          >
            <CardHeader>
              <div className={`w-12 h-12 rounded-lg ${mode.bgColor} flex items-center justify-center mb-4`}>
                <mode.icon className={`h-6 w-6 ${mode.color}`} />
              </div>
              <CardTitle>{mode.title}</CardTitle>
              <CardDescription>{mode.description}</CardDescription>
            </CardHeader>
          </Card>
        ))}
      </div>

      {/* Quick Tips */}
      <Card className="bg-muted/50">
        <CardContent className="pt-6">
          <p className="text-center text-muted-foreground">
            💡 Click the <span className="font-semibold">plus button</span> or press <kbd className="px-2 py-1 text-xs bg-background rounded">Ctrl+N</kbd> to create a new entry
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
```

### Talk to Your Diary (Same as Before)
[Previous Talk to Your Diary implementation remains the same]

### Memories & Settings Pages (Same as Before)
[Previous Memories and Settings implementations remain the same]

## Key Interactions Flow

1. **Creating Entries**:
   - Click plus button (floating) or "New Entry" in sidebar
   - Type or click microphone to record
   - One click creates all 3 versions (raw, enhanced, structured)

2. **Viewing Entries**:
   - Click "View Entries" in sidebar
   - See list on left, details on right (like email apps)
   - Filter by mode (all/raw/enhanced/structured)

3. **Pattern Discovery**:
   - Diamond button appears after 30 entries
   - Click to see pattern bubbles
   - Click pattern to see example entries

## Keyboard Shortcuts
```javascript
// utils/shortcuts.js
export function setupKeyboardShortcuts(navigate) {
  document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + N: New Entry
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
      e.preventDefault()
      navigate('/new')
    }
    
    // Ctrl/Cmd + E: View Entries
    if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
      e.preventDefault()
      navigate('/entries')
    }
    
    // Ctrl/Cmd + T: Talk to Diary
    if ((e.ctrlKey || e.metaKey) && e.key === 't') {
      e.preventDefault()
      navigate('/talk')
    }
  })
}
```

## Milestone Popups & Celebrations

### Pattern Unlock Celebration (30 Entries)
```jsx
// components/PatternUnlockCelebration.tsx
import { useEffect } from 'react'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Diamond, Sparkles } from 'lucide-react'
import confetti from 'canvas-confetti'

export function PatternUnlockCelebration({ open, onClose }) {
  useEffect(() => {
    if (open) {
      // Trigger confetti animation
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#6366F1', '#F472B6', '#FB923C']
      })
    }
  }, [open])

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md text-center">
        <div className="flex flex-col items-center space-y-4 py-6">
          <div className="relative">
            <Diamond className="h-16 w-16 text-primary animate-bounce" />
            <Sparkles className="h-8 w-8 text-secondary absolute -top-2 -right-2 animate-pulse" />
          </div>
          
          <h2 className="text-2xl font-bold">Pattern Insights Unlocked!</h2>
          
          <p className="text-muted-foreground max-w-sm">
            Congratulations! You've reached 30 entries. Your diary can now identify 
            recurring themes and patterns in your thoughts.
          </p>
          
          <Button onClick={onClose} size="lg" className="mt-4">
            Explore Patterns
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
```

### Buy Me a Coffee Popup
```jsx
// components/CoffeePopup.tsx
import { Dialog, DialogContent } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Coffee, Heart } from 'lucide-react'

export function CoffeePopup({ open, onClose, onSupport }) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <div className="flex flex-col items-center space-y-4 py-6">
          <div className="flex items-center gap-2">
            <Coffee className="h-12 w-12 text-orange-500" />
            <Heart className="h-8 w-8 text-red-500 animate-pulse" />
          </div>
          
          <h2 className="text-xl font-bold text-center">
            Enjoying Your Journal?
          </h2>
          
          <p className="text-muted-foreground text-center max-w-sm">
            You've been using Personal Journal for 7 days! If this app has helped 
            you reflect and grow, consider supporting its development.
          </p>
          
          <p className="text-sm text-muted-foreground text-center">
            This is open-source software made with love ❤️
          </p>
          
          <div className="flex gap-3 mt-4">
            <Button 
              onClick={onSupport}
              className="bg-gradient-to-r from-orange-500 to-orange-600"
            >
              <Coffee className="mr-2 h-4 w-4" />
              Buy Me a Coffee
            </Button>
            <Button variant="outline" onClick={onClose}>
              Maybe Later
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
```

### Integration in Main Layout
```jsx
// app/layout.tsx (additions)
import { PatternUnlockCelebration } from '@/components/PatternUnlockCelebration'
import { CoffeePopup } from '@/components/CoffeePopup'

export default function RootLayout({ children }) {
  const [showPatternCelebration, setShowPatternCelebration] = useState(false)
  const [showCoffeePopup, setShowCoffeePopup] = useState(false)
  
  // Check milestones on app load
  useEffect(() => {
    checkMilestones()
  }, [])
  
  const checkMilestones = async () => {
    const milestones = await api.checkMilestones()
    milestones.data.forEach(milestone => {
      if (milestone.type === 'pattern_unlock') {
        setShowPatternCelebration(true)
      } else if (milestone.type === 'coffee') {
        setShowCoffeePopup(true)
      }
    })
  }
  
  const handleCoffeeSupport = () => {
    window.open('https://buymeacoffee.com/yourhandle', '_blank')
    api.dismissMilestone('coffee')
    setShowCoffeePopup(false)
  }
  
  const handleCoffeeDismiss = () => {
    api.dismissMilestone('coffee')
    setShowCoffeePopup(false)
  }
  
  return (
    <div className="flex h-screen bg-background">
      {/* ... existing layout ... */}
      
      {/* Milestone Popups */}
      <PatternUnlockCelebration
        open={showPatternCelebration}
        onClose={() => {
          setShowPatternCelebration(false)
          navigate('/patterns')
        }}
      />
      
      <CoffeePopup
        open={showCoffeePopup}
        onClose={handleCoffeeDismiss}
        onSupport={handleCoffeeSupport}
      />
    </div>
  )
}
```

### Updated Whisper Service with State Notifications
```python
# whisper_service.py (additions)
def process_recording(self):
    try:
        # Notify frontend of state changes
        print("STATE:processing", file=sys.stdout)
        sys.stdout.flush()
        
        # Convert to numpy array
        audio_data = np.concatenate(self.recording_data, axis=0)
        
        # ... audio processing ...
        
        # Notify transcribing state
        print("STATE:transcribing", file=sys.stdout)
        sys.stdout.flush()
        
        # Transcribe
        result = self.model.transcribe(audio_np, fp16=False)
        transcribed_text = result["text"].strip()
        
        # Send transcription
        print(f"TRANSCRIPTION:{transcribed_text}")
        sys.stdout.flush()
        
    except Exception as e:
        print(f"ERROR: Transcription failed: {e}", file=sys.stderr)
        print("STATE:idle", file=sys.stdout)
        sys.stdout.flush()
```

### Electron Main Process Updates
```javascript
// electron/main.js (additions)
pythonProcess.stdout.on('data', (data) => {
  const message = data.toString()
  
  if (message.includes('TRANSCRIPTION:')) {
    const text = message.split('TRANSCRIPTION:')[1].trim()
    mainWindow.webContents.send('transcription-complete', text)
  } else if (message.includes('STATE:')) {
    const state = message.split('STATE:')[1].trim()
    mainWindow.webContents.send('transcription-state', state)
  }
})

// Preload additions
contextBridge.exposeInMainWorld('electron', {
  transcription: {
    // ... existing methods ...
    onStateChange: (callback) => ipcRenderer.on('transcription-state', (event, state) => callback(state))
  }
})
```

## Summary

This design provides:
- **Persistent left sidebar** like Notion for easy navigation
- **Floating plus button** for quick entry creation
- **Voice-first entry** with text fallback
- **Three modes** matching backend (raw, enhanced, structured)
- **Pattern insights** as diamond button after 30 entries
- **Clean entry browsing** with list/detail view

The flow is intuitive: Create → View → Discover Patterns → Talk to Diary for deeper insights.
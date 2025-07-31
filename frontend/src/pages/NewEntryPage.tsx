import { useState, useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Mic, MicOff, Loader2, Keyboard, CheckCircle, Plus, FileText, Pen, BookOpen, Sparkles, Edit3, Save, X } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '@/lib/api'
import { wsClient } from '@/lib/websocket'
import type { STTState, TranscriptionResult } from '@/lib/websocket'

// Recording states based on backend implementation
const RecordingState = {
  IDLE: 'idle',
  RECORDING: 'recording',
  PROCESSING: 'processing',
  TRANSCRIBING: 'transcribing',
  ENHANCING: 'enhancing',
  SUCCESS: 'success'
}

// View modes configuration (same as home page)
const viewModes = [
  {
    icon: FileText,
    title: "Raw Transcription",
    description: "Your exact words, unfiltered and authentic",
    gradient: "from-blue-500 to-blue-600",
    mode: "raw"
  },
  {
    icon: Pen,
    title: "Enhanced Style", 
    description: "Improved grammar and tone while preserving your intent",
    gradient: "from-purple-500 to-pink-500",
    mode: "enhanced"
  },
  {
    icon: BookOpen,
    title: "Structured Summary",
    description: "Organized into coherent themes and key points", 
    gradient: "from-emerald-500 to-teal-500",
    mode: "structured"
  }
]

// Quirky loading messages
const loadingMessages = [
  "Your memories are being created...",
  "Your voice is heard...", 
  "Weaving your thoughts together...",
  "AI is polishing your words...",
  "Crafting your story...",
  "Organizing your thoughts...",
  "Making magic happen...",
  "Your journal is coming to life...",
  "Processing your wisdom...",
  "Creating something beautiful..."
]

interface CreatedEntries {
  raw: {
    id: number
    raw_text: string
    timestamp: string
  }
  enhanced?: {
    id: number
    enhanced_text: string
  }
  structured?: {
    id: number
    structured_summary: string
  }
}

function NewEntryPage() {
  const location = useLocation()
  const [text, setText] = useState('')
  const [recordingState, setRecordingState] = useState(RecordingState.IDLE)
  const [isProcessing, setIsProcessing] = useState(false)
  const [createdEntries, setCreatedEntries] = useState<CreatedEntries | null>(null)
  const [currentHotkey, setCurrentHotkey] = useState('F8')
  const [isConnected, setIsConnected] = useState(false)
  const [processingJobId, setProcessingJobId] = useState<string | null>(null)
  const [recordingSource, setRecordingSource] = useState<'hotkey' | 'button' | null>(null)
  
  // New state for UI flow
  const [showInputUI, setShowInputUI] = useState(true)
  const [showResults, setShowResults] = useState(false)
  const [currentLoadingMessage, setCurrentLoadingMessage] = useState('')
  
  // Edit state
  const [editingCard, setEditingCard] = useState<string | null>(null)
  const [showOverlay, setShowOverlay] = useState(false)
  const [overlayContent, setOverlayContent] = useState('')
  const [overlayMode, setOverlayMode] = useState('')
  
  const { toast } = useToast()
  const textAreaRef = useRef<HTMLTextAreaElement>(null)
  const isStartingRef = useRef(false) // Prevent multiple simultaneous recording attempts

  // Helper function to ensure toast content is valid
  const safeToast = (params: Parameters<typeof toast>[0]) => {
    if (!params.title?.trim() && !params.description?.toString()?.trim()) {
      return // Don't show empty toasts
    }
    // Add shorter duration for quicker dismissal
    toast({
      ...params,
      duration: 2000 // 2 seconds for quick dismissal
    })
  }

  // Reset state when navigating back to /new (sidebar click)
  useEffect(() => {
    if (location.pathname === '/new') {
      // Only reset if we're in results view, not during normal usage
      if (showResults && !isProcessing) {
        startNewEntry()
      }
    }
  }, [location.pathname])

  // WebSocket setup and event handlers
  useEffect(() => {
    // Subscribe to connection changes first (before connecting)
    const unsubscribeConnection = wsClient.onConnectionChange((connected) => {
      console.log('WebSocket connection state changed:', connected)
      setIsConnected(connected)
      if (connected) {
        // Subscribe to STT channels
        wsClient.subscribeToChannels(['stt', 'recording', 'transcription'])
      }
    })

    // Connect to WebSocket with retry logic
    const connectWithRetry = async () => {
      try {
        await wsClient.connect()
        // Check if connected and update state
        if (wsClient.isConnected()) {
          console.log('WebSocket connected successfully')
          setIsConnected(true)
          wsClient.subscribeToChannels(['stt', 'recording', 'transcription'])
        }
      } catch (error) {
        console.error('Initial WebSocket connection failed:', error)
        // Don't show toast on initial connection failure - let user trigger manually
        setIsConnected(false)
      }
    }
    
    connectWithRetry()

    // Subscribe to state changes
    const unsubscribeState = wsClient.onStateChange((state: STTState) => {
      console.log('STT State:', state)
      // Reset the starting flag when we get any state update from backend
      isStartingRef.current = false
      
      // Map backend states to frontend states
      if (state.state === 'idle') {
        setRecordingState(RecordingState.IDLE)
      } else if (state.state === 'recording') {
        setRecordingState(RecordingState.RECORDING)
      } else if (state.state === 'processing') {
        setRecordingState(RecordingState.PROCESSING)
      } else if (state.state === 'transcribing') {
        setRecordingState(RecordingState.TRANSCRIBING)
      }
    })

    // Subscribe to transcription results
    const unsubscribeTranscription = wsClient.onTranscription((result: TranscriptionResult) => {
      console.log('Transcription result:', result)
      if (result.text) {
        // Accumulate text with space continuation
        setText(prevText => {
          if (!prevText) return result.text
          // Add space for continuation
          return prevText + ' ' + result.text
        })
        setRecordingState(RecordingState.IDLE)
      }
    })

    // Subscribe to errors
    const unsubscribeError = wsClient.onError((error: string) => {
      console.error('WebSocket error:', error)
      // Only show toast for critical errors, not connection state changes or recording state conflicts
      const shouldSkipError = error.includes('connection') || 
                             error.includes('WebSocket') || 
                             error.includes('Cannot start recording in state') ||
                             error.includes('Failed to start STT recording') ||
                             !error.trim()
      
      if (!shouldSkipError) {
        safeToast({
          title: "Recording Error",
          description: error.trim() || "An unknown error occurred",
          variant: "destructive"
        })
      }
      setRecordingState(RecordingState.IDLE)
    })

    // Load current hotkey from preferences
    loadHotkeyPreference()

    // Cleanup on unmount
    return () => {
      unsubscribeConnection()
      unsubscribeState()
      unsubscribeTranscription()
      unsubscribeError()
    }
  }, [toast])

  // Listen for F8 hotkey press events (HOLD to record)
  useEffect(() => {
    const handleKeyDown = async (e: KeyboardEvent) => {
      // Check if it's the recording hotkey (F8)
      if (e.key === currentHotkey || e.key.toUpperCase() === currentHotkey.toUpperCase()) {
        if (!e.repeat && recordingState === RecordingState.IDLE) {
          e.preventDefault()
          setRecordingSource('hotkey')
          await startRecording()
        } else if (e.repeat) {
          // Prevent repeated F8 presses while already recording
          e.preventDefault()
        }
      }
    }

    const handleKeyUp = (e: KeyboardEvent) => {
      // Check if it's the recording hotkey (F8)
      if (e.key === currentHotkey || e.key.toUpperCase() === currentHotkey.toUpperCase()) {
        if (recordingState === RecordingState.RECORDING) {
          e.preventDefault()
          stopRecording()
          setRecordingSource(null)
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('keyup', handleKeyUp)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('keyup', handleKeyUp)
    }
  }, [currentHotkey, recordingState])

  const loadHotkeyPreference = async () => {
    try {
      const response = await api.getPreferences()
      if (response.success && response.data && response.data.preferences) {
        const hotkey = response.data.preferences.find((pref: any) => pref.key === 'recording_hotkey')
        if (hotkey && hotkey.value) {
          setCurrentHotkey(hotkey.value)
        }
      }
    } catch (error) {
      console.error('Failed to load hotkey preference:', error)
    }
  }

  const startRecording = async () => {
    // Only proceed if we're truly idle and not already starting
    if (isStartingRef.current || recordingState !== RecordingState.IDLE) {
      return
    }
    
    // Check actual WebSocket connection state
    if (!wsClient.isConnected()) {
      safeToast({
        title: "Connection Error",
        description: "Please ensure connection is established",
        variant: "destructive"
      })
      return
    }
    
    isStartingRef.current = true
    // Don't reset the flag immediately - let the state change handler reset it
    wsClient.startRecording()
  }

  const stopRecording = () => {
    if (recordingState === RecordingState.RECORDING) {
      setRecordingState(RecordingState.PROCESSING)
      wsClient.stopRecording()
    }
  }

  const toggleRecording = async () => {
    if (recordingState === RecordingState.IDLE) {
      setRecordingSource('button')
      await startRecording()
    } else if (recordingState === RecordingState.RECORDING) {
      stopRecording()
      setRecordingSource(null)
    }
  }

  // Loading message cycling effect
  useEffect(() => {
    let interval: NodeJS.Timeout
    
    if (isProcessing && !showResults) {
      // Cycle through loading messages
      let messageIndex = 0
      setCurrentLoadingMessage(loadingMessages[0])
      
      interval = setInterval(() => {
        messageIndex = (messageIndex + 1) % loadingMessages.length
        setCurrentLoadingMessage(loadingMessages[messageIndex])
      }, 2000) // Change message every 2 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isProcessing, showResults])

  const createEntries = async () => {
    if (!text.trim()) {
      safeToast({
        title: "No content",
        description: "Please record or type something first",
        variant: "destructive"
      })
      return
    }

    // Hide input UI with animation
    setShowInputUI(false)
    setIsProcessing(true)
    setRecordingState(RecordingState.ENHANCING)
    setCreatedEntries(null)
    
    try {
      // Create entry with all three modes
      const response = await api.createAndProcessEntry(
        text.trim(),
        ['enhanced', 'structured']
      )
      
      if (response.success && response.data) {
        const { raw_entry, job_id } = response.data
        
        // Store initial entry data
        setCreatedEntries({
          raw: {
            id: raw_entry.id,
            raw_text: raw_entry.raw_text,
            timestamp: raw_entry.timestamp
          }
        })
        
        // Store job ID for status tracking (use master job ID)
        setProcessingJobId(job_id)
        
        // Poll for job completion
        if (job_id) {
          pollJobStatus(job_id)
        }
        
        // Show initial success toast
        safeToast({
          title: "Entry created!",
          description: "Processing enhanced versions...",
        })
      } else {
        throw new Error(response.error || 'Failed to create entry')
      }
    } catch (error) {
      setRecordingState(RecordingState.IDLE)
      safeToast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to create entries",
        variant: "destructive"
      })
      setIsProcessing(false)
    }
  }

  const pollJobStatus = async (jobId: string) => {
    const maxAttempts = 30
    const pollInterval = 1000
    let attempts = 0

    const poll = async () => {
      if (attempts >= maxAttempts) {
        setRecordingState(RecordingState.IDLE)
        setIsProcessing(false)
        safeToast({
          title: "Processing timeout",
          description: "Entry processing is taking longer than expected",
          variant: "destructive"
        })
        return
      }

      attempts++

      try {
        const response = await api.getJobStatus(jobId)
        if (response.success && response.data) {
          const { status, result, error } = response.data

          if (status === 'completed' && result) {
            // Update with processed entries
            setCreatedEntries(prev => ({
              ...prev!,
              enhanced: result.enhanced ? {
                id: result.entry_id,
                enhanced_text: result.enhanced
              } : undefined,
              structured: result.structured ? {
                id: result.entry_id,
                structured_summary: result.structured
              } : undefined
            }))

            // Show success state and results
            setRecordingState(RecordingState.SUCCESS)
            setShowResults(true)
            setTimeout(() => setRecordingState(RecordingState.IDLE), 2000)
            
            // Success toast with checkmarks
            safeToast({
              title: "✓ Entries created!",
              description: (
                <div className="space-y-1 mt-2">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-3 w-3 text-green-500" />
                    <span className="text-sm">Raw transcription saved</span>
                  </div>
                  {result.enhanced && (
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-3 w-3 text-green-500" />
                      <span className="text-sm">Enhanced style created</span>
                    </div>
                  )}
                  {result.structured && (
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-3 w-3 text-green-500" />
                      <span className="text-sm">Structured summary generated</span>
                    </div>
                  )}
                </div>
              ),
            })
            
            // Clear for next entry
            setText('')
            setIsProcessing(false)
            setProcessingJobId(null)
            
          } else if (status === 'failed') {
            throw new Error(error || 'Processing failed')
          } else {
            // Still processing, continue polling
            setTimeout(poll, pollInterval)
          }
        }
      } catch (error) {
        setRecordingState(RecordingState.IDLE)
        setIsProcessing(false)
        safeToast({
          title: "Error",
          description: "Failed to check processing status",
          variant: "destructive"
        })
      }
    }

    poll()
  }

  const startNewEntry = () => {
    // Reset all state
    setText('')
    setCreatedEntries(null)
    setIsProcessing(false)
    setProcessingJobId(null)
    setRecordingState(RecordingState.IDLE)
    setShowInputUI(true)
    setShowResults(false)
    setCurrentLoadingMessage('')
    setEditingCard(null)
    setShowOverlay(false)
  }

  const backToEdit = () => {
    // Return to edit mode but keep the original raw text
    const originalText = createdEntries?.raw?.raw_text || ''
    setText(originalText)
    setCreatedEntries(null)
    setIsProcessing(false)
    setProcessingJobId(null)
    setRecordingState(RecordingState.IDLE)
    setShowInputUI(true)
    setShowResults(false)
    setCurrentLoadingMessage('')
    setEditingCard(null)
    setShowOverlay(false)
  }

  const handleCardEdit = (mode: string) => {
    let content = ''
    if (mode === 'raw' && createdEntries?.raw) {
      content = createdEntries.raw.raw_text
    } else if (mode === 'enhanced' && createdEntries?.enhanced) {
      content = createdEntries.enhanced.enhanced_text
    } else if (mode === 'structured' && createdEntries?.structured) {
      content = createdEntries.structured.structured_summary
    }
    
    setOverlayContent(content)
    setOverlayMode(mode)
    setShowOverlay(true)
  }

  const handleSaveEdit = () => {
    if (!createdEntries) return
    
    const updatedEntries = { ...createdEntries }
    
    if (overlayMode === 'raw' && updatedEntries.raw) {
      updatedEntries.raw.raw_text = overlayContent
    } else if (overlayMode === 'enhanced' && updatedEntries.enhanced) {
      updatedEntries.enhanced.enhanced_text = overlayContent
    } else if (overlayMode === 'structured' && updatedEntries.structured) {
      updatedEntries.structured.structured_summary = overlayContent
    }
    
    setCreatedEntries(updatedEntries)
    setShowOverlay(false)
    setOverlayContent('')
    setOverlayMode('')
  }

  const handleAddToDiary = async () => {
    if (!createdEntries) return
    
    try {
      // Here you would implement the API call to save final entries to database
      // For now, just show success message
      safeToast({
        title: "✓ Added to diary!",
        description: "Your entries have been saved successfully",
      })
      
      // Reset to start new entry
      setTimeout(() => {
        startNewEntry()
      }, 2000)
      
    } catch (error) {
      safeToast({
        title: "Error",
        description: "Failed to add entries to diary",
        variant: "destructive"
      })
    }
  }

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength).trim() + '...'
  }

  const getStateMessage = () => {
    switch (recordingState) {
      case RecordingState.RECORDING:
        if (recordingSource === 'hotkey') {
          return `Recording... Release ${currentHotkey} to stop`
        } else {
          return "Recording... Click button to stop"
        }
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
    <div className="h-screen flex flex-col p-4 md:p-6 max-w-6xl mx-auto overflow-hidden relative">
      {/* Header - Always shown */}
      <div className="flex items-center justify-between mb-4 min-h-[40px]">
        <h2 className="text-2xl font-bold text-white">New Entry</h2>
        <div className="flex items-center gap-2 flex-shrink-0">
          <Badge 
            className={`flex items-center gap-2 ${
              isConnected
                ? 'bg-green-500/20 border border-green-500/30 text-green-400' 
                : 'bg-red-500/20 border border-red-500/30 text-red-400 animate-pulse'
            }`}
          >
            <div 
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            {isConnected ? 'Connected' : 'Disconnected'}
          </Badge>
          {recordingState !== RecordingState.IDLE && showInputUI && (
            <div className="relative overflow-hidden px-4 py-2 rounded-md font-medium shadow-md transition-all duration-300 flex items-center justify-center bg-primary/10 border border-primary/20 text-primary max-w-xs shrink-0">
              <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-secondary/10 opacity-70 transition-opacity duration-300" />
              <div className="relative z-10 flex items-center gap-2">
                {getStateIcon()}
                <span className="text-sm font-medium truncate">{getStateMessage()}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Input UI - Hide with animation when processing */}
      <AnimatePresence>
        {showInputUI && (
          <motion.div
            initial={{ opacity: 1, scale: 1 }}
            exit={{ 
              opacity: 0, 
              scale: 0.95,
              y: -20,
              transition: { duration: 0.4, ease: "easeInOut" }
            }}
            className="flex-1 flex flex-col overflow-hidden"
          >
            <Card className="p-6 flex-1 flex flex-col overflow-hidden">
              <div className="relative flex-1 flex flex-col overflow-hidden">
                <Textarea
                  ref={textAreaRef}
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder={`Start typing or hold ${currentHotkey} to speak...`}
                  className="flex-1 resize-none pr-16 text-sm leading-relaxed text-white placeholder:text-gray-400 bg-transparent border-border focus:border-primary/50 transition-colors max-w-none w-full"
                  disabled={recordingState !== RecordingState.IDLE || isProcessing}
                />

                {/* Voice Recording Button & Hotkey Indicator */}
                <div className="absolute bottom-4 right-4 flex flex-col items-center gap-2 pointer-events-auto">
                  <button
                    className={`relative overflow-hidden group p-3 rounded-full font-medium shadow-md hover:shadow-lg hover:scale-[1.02] transition-all duration-300 cursor-pointer inline-flex items-center justify-center focus:outline-none ${
                      recordingState === RecordingState.RECORDING 
                        ? 'bg-red-500/20 border border-red-500/30 text-red-500 animate-pulse' 
                        : 'bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20'
                    }`}
                    onClick={toggleRecording}
                    disabled={!isConnected || (recordingState !== RecordingState.IDLE && recordingState !== RecordingState.RECORDING)}
                  >
                    <div className={`absolute inset-0 bg-gradient-to-r ${
                      recordingState === RecordingState.RECORDING 
                        ? 'from-red-500/10 to-red-400/10' 
                        : 'from-primary/10 to-secondary/10'
                    } opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
                    
                    <span className="relative z-10">
                      {recordingState === RecordingState.RECORDING ? (
                        <div className="flex items-center justify-center w-5 h-5">
                          <div className="w-3 h-3 bg-red-500 rounded-sm"></div>
                        </div>
                      ) : (
                        <Mic className="h-5 w-5" />
                      )}
                    </span>
                  </button>
                  <div className="flex flex-col items-center gap-1 text-xs text-muted-foreground">
                    <span>{recordingState === RecordingState.RECORDING ? 'Click to stop' : 'Click to start'}</span>
                    <div className="flex items-center gap-1">
                      <Keyboard className="h-3 w-3" />
                      <span>Hold {currentHotkey}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Word count */}
              <div className="mt-2 text-sm text-muted-foreground">
                {text.trim().split(/\s+/).filter(Boolean).length} words
              </div>

              {/* Action Buttons */}
              <div className="mt-4 flex justify-between items-center">
                <button 
                  onClick={() => setText('')}
                  disabled={isProcessing || recordingState !== RecordingState.IDLE}
                  className="relative overflow-hidden group px-6 py-3 rounded-md font-medium shadow-md hover:shadow-lg hover:scale-[1.02] transition-all duration-300 cursor-pointer inline-flex items-center justify-center bg-gray-500/10 border border-gray-500/20 text-gray-400 hover:bg-gray-500/20 hover:text-gray-300"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-gray-500/10 to-gray-400/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <span className="relative z-10 font-medium transition-colors duration-300">
                    Clear All
                  </span>
                </button>

                <button 
                  onClick={createEntries}
                  disabled={isProcessing || !text.trim() || recordingState !== RecordingState.IDLE}
                  className="relative overflow-hidden group px-8 py-3 rounded-md font-medium shadow-md hover:shadow-lg hover:scale-[1.02] transition-all duration-300 cursor-pointer inline-flex items-center justify-center bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-secondary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <span className="relative z-10 text-primary font-medium group-hover:text-primary transition-colors duration-300 flex items-center">
                    {isProcessing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Create All Three Entries
                  </span>
                </button>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading State - Show during processing */}
      <AnimatePresence>
        {isProcessing && !showResults && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.4, ease: "easeInOut" }}
            className="flex-1 flex items-center justify-center"
          >
            <div className="text-center space-y-6">
              <motion.div
                animate={{ 
                  rotate: 360,
                  scale: [1, 1.1, 1]
                }}
                transition={{ 
                  rotate: { duration: 2, repeat: Infinity, ease: "linear" },
                  scale: { duration: 2, repeat: Infinity, ease: "easeInOut" }
                }}
              >
                <Sparkles className="w-16 h-16 text-primary mx-auto" />
              </motion.div>
              
              <motion.p
                key={currentLoadingMessage}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.5 }}
                className="text-xl text-white font-medium"
              >
                {currentLoadingMessage}
              </motion.p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results Cards - Show after completion */}
      <AnimatePresence>
        {showResults && createdEntries && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="flex-1 flex flex-col overflow-visible px-4 py-4"
          >
            <div className="grid md:grid-cols-3 gap-6 flex-1 mb-6">
              {viewModes.map((mode, index) => {
                let content = ''
                let hasContent = false
                
                if (mode.mode === 'raw' && createdEntries.raw) {
                  content = createdEntries.raw.raw_text
                  hasContent = true
                } else if (mode.mode === 'enhanced' && createdEntries.enhanced) {
                  content = createdEntries.enhanced.enhanced_text
                  hasContent = true
                } else if (mode.mode === 'structured' && createdEntries.structured) {
                  content = createdEntries.structured.structured_summary
                  hasContent = true
                }
                
                // Truncate text to fit without scroll - estimate ~500 chars for good fit
                const displayContent = hasContent ? truncateText(content, 500) : 'Processing...'
                
                return (
                  <motion.div
                    key={mode.mode}
                    initial={{ opacity: 0, y: 30, scale: 0.9 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ 
                      duration: 0.5, 
                      delay: index * 0.1,
                      type: "spring",
                      stiffness: 300,
                      damping: 24
                    }}
                    whileHover={{ 
                      y: -6,
                      scale: 1.015,
                      transition: {
                        type: "spring",
                        stiffness: 400,
                        damping: 10
                      }
                    }}
                  >
                    <Card 
                      className="h-full bg-card/50 backdrop-blur-sm border-border/50 hover:border-primary/30 transition-all duration-300 overflow-hidden group relative cursor-pointer"
                      onClick={() => handleCardEdit(mode.mode)}
                    >
                      {/* Gradient overlay */}
                      <div className={`absolute inset-0 bg-gradient-to-br ${mode.gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-300`} />
                      
                      {/* Shimmer effect */}
                      <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/10 to-transparent group-hover:translate-x-full transition-transform duration-700" />
                      
                      <CardHeader className="pb-2 relative">
                        <motion.div 
                          className={`w-12 h-12 rounded-xl bg-gradient-to-br ${mode.gradient} flex items-center justify-center mb-4 shadow-lg shadow-primary/20 relative`}
                          whileHover={{ 
                            scale: 1.1,
                            rotate: 5
                          }}
                          transition={{ type: "spring", stiffness: 300, damping: 10 }}
                        >
                          <mode.icon className="h-6 w-6 text-white" />
                          <div className={`absolute inset-0 rounded-xl bg-gradient-to-br ${mode.gradient} opacity-10`} />
                        </motion.div>
                        
                        <div className="flex items-center justify-between mb-1">
                          <CardTitle className="text-lg font-bold text-white group-hover:text-primary transition-colors duration-300">
                            {mode.title}
                          </CardTitle>
                          
                          {/* Edit Icon - inline with title */}
                          <div 
                            className="opacity-0 group-hover:opacity-100 transition-opacity duration-300 cursor-pointer"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleCardEdit(mode.mode)
                            }}
                          >
                            <div className="bg-primary/20 backdrop-blur-sm rounded-full p-1.5 border border-primary/30 hover:bg-primary/30 transition-colors">
                              <Edit3 className="h-3.5 w-3.5 text-primary" />
                            </div>
                          </div>
                        </div>
                        <CardDescription className="text-gray-400 text-xs leading-tight mb-3">
                          {mode.description}
                        </CardDescription>
                      </CardHeader>
                      
                      <CardContent className="relative flex-1 pt-0">
                        <div className="bg-muted/20 rounded-lg p-4 h-full min-h-[280px] flex flex-col">
                          <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap flex-1">
                            {displayContent}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                )
              })}
            </div>
            
            {/* Action Buttons */}
            <div className="flex justify-center gap-4">
              {/* Back to Edit Button */}
              <motion.button
                onClick={backToEdit}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="relative overflow-hidden group px-6 py-4 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer inline-flex items-center justify-center bg-gray-500/10 border border-gray-500/20 text-gray-400 hover:bg-gray-500/20 hover:text-gray-300"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-gray-500/10 to-gray-400/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <span className="relative z-10 font-semibold transition-colors duration-300 flex items-center">
                  <Edit3 className="mr-2 h-5 w-5" />
                  Back to Edit
                </span>
              </motion.button>

              {/* Add to Diary Button */}
              <motion.button
                onClick={handleAddToDiary}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.4 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="relative overflow-hidden group px-8 py-4 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer inline-flex items-center justify-center bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-secondary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <span className="relative z-10 text-primary font-semibold group-hover:text-primary transition-colors duration-300 flex items-center">
                  <BookOpen className="mr-2 h-5 w-5" />
                  Add to Diary
                </span>
              </motion.button>

              {/* Start Over Button */}
              <motion.button
                onClick={startNewEntry}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.5 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="relative overflow-hidden group px-6 py-4 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer inline-flex items-center justify-center bg-gray-500/10 border border-gray-500/20 text-gray-400 hover:bg-gray-500/20 hover:text-gray-300"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-gray-500/10 to-gray-400/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <span className="relative z-10 font-semibold transition-colors duration-300 flex items-center">
                  <Plus className="mr-2 h-5 w-5" />
                  Start Over
                </span>
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Overlay Edit Modal */}
      <AnimatePresence>
        {showOverlay && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowOverlay(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.3 }}
              className="bg-card/90 backdrop-blur-xl border border-border/50 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[80vh] flex flex-col overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-border/50">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${
                    viewModes.find(m => m.mode === overlayMode)?.gradient || 'from-primary to-secondary'
                  } flex items-center justify-center`}>
                    {overlayMode === 'raw' && <FileText className="h-5 w-5 text-white" />}
                    {overlayMode === 'enhanced' && <Pen className="h-5 w-5 text-white" />}
                    {overlayMode === 'structured' && <BookOpen className="h-5 w-5 text-white" />}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">
                      Edit {viewModes.find(m => m.mode === overlayMode)?.title}
                    </h3>
                    <p className="text-sm text-gray-400">
                      Make changes to your {overlayMode} entry
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowOverlay(false)}
                  className="p-2 rounded-full hover:bg-muted/50 transition-colors"
                >
                  <X className="h-5 w-5 text-gray-400" />
                </button>
              </div>
              
              {/* Content */}
              <div className="flex-1 p-6 overflow-hidden">
                <Textarea
                  value={overlayContent}
                  onChange={(e) => setOverlayContent(e.target.value)}
                  className="w-full h-full min-h-[400px] resize-none text-sm leading-relaxed text-white placeholder:text-gray-400 bg-muted/20 border-border focus:border-primary/50 transition-colors"
                  placeholder="Edit your content here..."
                />
              </div>
              
              {/* Footer */}
              <div className="flex items-center justify-between p-6 border-t border-border/50">
                <div className="text-sm text-gray-400">
                  {overlayContent.trim().split(/\s+/).filter(Boolean).length} words
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setShowOverlay(false)}
                    className="px-4 py-2 rounded-lg border border-border/50 text-gray-400 hover:bg-muted/50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveEdit}
                    className="px-6 py-2 rounded-lg bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 transition-colors flex items-center gap-2"
                  >
                    <Save className="h-4 w-4" />
                    Save Changes
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default NewEntryPage
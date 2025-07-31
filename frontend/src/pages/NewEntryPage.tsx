import { useState, useEffect, useRef } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Mic, MicOff, Loader2, Keyboard, CheckCircle } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
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
  const [text, setText] = useState('')
  const [recordingState, setRecordingState] = useState(RecordingState.IDLE)
  const [isProcessing, setIsProcessing] = useState(false)
  const [createdEntries, setCreatedEntries] = useState<CreatedEntries | null>(null)
  const [currentHotkey, setCurrentHotkey] = useState('F8')
  const [isConnected, setIsConnected] = useState(false)
  const [processingJobId, setProcessingJobId] = useState<string | null>(null)
  const [recordingSource, setRecordingSource] = useState<'hotkey' | 'button' | null>(null)
  const { toast } = useToast()
  const textAreaRef = useRef<HTMLTextAreaElement>(null)
  const isStartingRef = useRef(false) // Prevent multiple simultaneous recording attempts

  // Helper function to ensure toast content is valid
  const safeToast = (params: Parameters<typeof toast>[0]) => {
    if (!params.title?.trim() && !params.description?.toString()?.trim()) {
      return // Don't show empty toasts
    }
    toast(params)
  }

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
        // Accumulate text with proper paragraph separation
        setText(prevText => {
          if (!prevText) return result.text
          // Add double newline for paragraph separation
          return prevText + '\n\n' + result.text
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

  const createEntries = async () => {
    if (!text.trim()) {
      safeToast({
        title: "No content",
        description: "Please record or type something first",
        variant: "destructive"
      })
      return
    }

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
        const { entry, job_id } = response.data
        
        // Store initial entry data
        setCreatedEntries({
          raw: {
            id: entry.id,
            raw_text: entry.raw_text,
            timestamp: entry.timestamp
          }
        })
        
        // Store job ID for status tracking
        setProcessingJobId(job_id)
        
        // Poll for job completion
        pollJobStatus(job_id)
        
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

            // Show success state
            setRecordingState(RecordingState.SUCCESS)
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
          {recordingState !== RecordingState.IDLE && (
            <div className="relative overflow-hidden px-4 py-2 rounded-md font-medium shadow-md transition-all duration-300 flex items-center justify-center bg-primary/10 border border-primary/20 text-primary max-w-xs shrink-0">
              {/* Animated background */}
              <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-secondary/10 opacity-70 transition-opacity duration-300" />
              
              {/* Content */}
              <div className="relative z-10 flex items-center gap-2">
                {getStateIcon()}
                <span className="text-sm font-medium truncate">{getStateMessage()}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      <Card className="p-6 flex-1 flex flex-col overflow-hidden">
        <div className="relative flex-1 flex flex-col overflow-hidden">
          <Textarea
            ref={textAreaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={`Start typing or hold ${currentHotkey} to speak...`}
            className="flex-1 resize-none pr-16 text-sm leading-relaxed text-white placeholder:text-gray-400 bg-transparent border-border focus:border-primary/50 transition-colors"
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
              {/* Animated background on hover */}
              <div className={`absolute inset-0 bg-gradient-to-r ${
                recordingState === RecordingState.RECORDING 
                  ? 'from-red-500/10 to-red-400/10' 
                  : 'from-primary/10 to-secondary/10'
              } opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
              
              {/* Icon */}
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
            {/* Animated background on hover */}
            <div className="absolute inset-0 bg-gradient-to-r from-gray-500/10 to-gray-400/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            
            {/* Button text */}
            <span className="relative z-10 font-medium transition-colors duration-300">
              Clear All
            </span>
          </button>

          <button 
            onClick={createEntries}
            disabled={isProcessing || !text.trim() || recordingState !== RecordingState.IDLE}
            className="relative overflow-hidden group px-8 py-3 rounded-md font-medium shadow-md hover:shadow-lg hover:scale-[1.02] transition-all duration-300 cursor-pointer inline-flex items-center justify-center bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20"
          >
            {/* Animated background on hover */}
            <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-secondary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            
            {/* Button text */}
            <span className="relative z-10 text-primary font-medium group-hover:text-primary transition-colors duration-300 flex items-center">
              {isProcessing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create All Three Entries
            </span>
          </button>
        </div>
      </Card>

      {/* Preview Created Entries - Only show when not in writing mode */}
      {createdEntries && (
        <div className="mt-4 space-y-3 max-h-32 overflow-y-auto">
          <h3 className="text-sm font-semibold text-white">Created Entries:</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Card className="p-3 border-l-4 border-l-primary">
              <h4 className="font-medium mb-1 text-white text-xs">Raw</h4>
              <p className="text-xs text-muted-foreground line-clamp-2">{createdEntries.raw.raw_text}</p>
            </Card>
            
            {createdEntries.enhanced && (
              <Card className="p-3 border-l-4 border-l-secondary">
                <h4 className="font-medium mb-1 text-white text-xs">Enhanced</h4>
                <p className="text-xs text-muted-foreground line-clamp-2">{createdEntries.enhanced.enhanced_text}</p>
              </Card>
            )}
            
            {createdEntries.structured && (
              <Card className="p-3 border-l-4 border-l-accent">
                <h4 className="font-medium mb-1 text-white text-xs">Structured</h4>
                <p className="text-xs text-muted-foreground line-clamp-2">{createdEntries.structured.structured_summary}</p>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default NewEntryPage
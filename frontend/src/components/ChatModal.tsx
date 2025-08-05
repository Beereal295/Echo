import { useState, useEffect, useRef, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Mic, MicOff, Send, Volume2, X, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'
import { useSTT } from '@/hooks/useSTT'
import { motion, AnimatePresence } from 'framer-motion'
import { useToast } from '@/components/ui/use-toast'

// Typewriter Text Component for chat messages
interface TypewriterTextProps {
  text: string
  isActive: boolean
  className?: string
  onComplete?: () => void
}

function TypewriterText({ text, isActive, className = '', onComplete }: TypewriterTextProps) {
  const [displayedText, setDisplayedText] = useState('')
  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    if (!isActive) {
      setDisplayedText(text)
      setCurrentIndex(text.length)
      return
    }

    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayedText(text.slice(0, currentIndex + 1))
        setCurrentIndex(currentIndex + 1)
      }, 25) // Faster than the main card (25ms vs 80ms)

      return () => clearTimeout(timer)
    } else if (onComplete && currentIndex === text.length) {
      onComplete()
    }
  }, [currentIndex, text, isActive, onComplete])

  // Reset when text changes
  useEffect(() => {
    if (isActive) {
      setDisplayedText('')
      setCurrentIndex(0)
    } else {
      setDisplayedText(text)
      setCurrentIndex(text.length)
    }
  }, [text, isActive])

  return (
    <span className={className}>
      {displayedText}
      {isActive && currentIndex < text.length && (
        <motion.span
          animate={{ opacity: [1, 0] }}
          transition={{ duration: 0.8, repeat: Infinity }}
          className="text-primary"
        >
          |
        </motion.span>
      )}
    </span>
  )
}

interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isStreaming?: boolean
}

interface ChatModalProps {
  isOpen: boolean
  onClose: (transcription: string, duration: number, messageCount: number, searchQueries: string[]) => void
  onEndChat: (transcription: string, duration: number, messageCount: number, searchQueries: string[]) => void
  voiceEnabled: boolean
  onVoiceToggle: (enabled: boolean) => void
}

function ChatModal({ isOpen, onClose, onEndChat, voiceEnabled, onVoiceToggle }: ChatModalProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputText, setInputText] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingMessage, setProcessingMessage] = useState('')
  const [isToolCall, setIsToolCall] = useState(false)
  const [searchQueries, setSearchQueries] = useState<string[]>([])
  const [startTime, setStartTime] = useState<Date | null>(null)
  const [audioPlaying, setAudioPlaying] = useState(false)
  const [ttsInitialized, setTtsInitialized] = useState(false)
  const audioContextRef = useRef<AudioContext | null>(null)
  const currentAudioSourceRef = useRef<AudioBufferSourceNode | null>(null)
  const { toast } = useToast()

  // Helper function to ensure toast content is valid (same as NewEntryPage)
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
  
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const messageIdCounter = useRef(0)

  // STT integration - exact same as NewEntryPage
  const { 
    recordingState,
    startRecording, 
    stopRecording, 
    error: sttError,
    transcription: sttTranscription,
    isTranscribing,
    isRecording
  } = useSTT()

  // Load hotkey from preferences
  const [hotkey, setHotkey] = useState('F8')
  
  useEffect(() => {
    const loadHotkey = async () => {
      try {
        const response = await api.getPreferences()
        if (response.success && response.data?.preferences) {
          const hotkeyPref = response.data.preferences.find(p => p.key === 'hotkey')
          if (hotkeyPref) {
            setHotkey(hotkeyPref.value)
          }
        }
      } catch (error) {
        console.error('Failed to load hotkey:', error)
      }
    }
    loadHotkey()
  }, [])

  // Listen for hotkey press events (HOLD to record) - same as NewEntryPage
  useEffect(() => {
    const handleKeyDown = async (e: KeyboardEvent) => {
      // Check if it's the recording hotkey
      if (e.key === hotkey || e.key.toUpperCase() === hotkey.toUpperCase()) {
        if (!e.repeat && recordingState === 'idle') {
          e.preventDefault()
          await handleStartRecording()
        } else if (e.repeat) {
          // Prevent repeated key presses while already recording
          e.preventDefault()
        }
      }
    }

    const handleKeyUp = (e: KeyboardEvent) => {
      // Check if it's the recording hotkey
      if (e.key === hotkey || e.key.toUpperCase() === hotkey.toUpperCase()) {
        if (recordingState === 'recording') {
          e.preventDefault()
          handleStopRecording()
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('keyup', handleKeyUp)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('keyup', handleKeyUp)
    }
  }, [hotkey, recordingState])

  // Initialize modal with greeting
  useEffect(() => {
    if (isOpen) {
      initializeChat()
      if (voiceEnabled) {
        initializeTTS()
      }
    } else {
      // Reset state when modal closes
      setMessages([])
      setInputText('')
      setSearchQueries([])
      setStartTime(null)
      setTtsInitialized(false)
      // Stop any playing audio
      if (currentAudioSourceRef.current) {
        try {
          currentAudioSourceRef.current.stop()
        } catch (e) {
          // Audio might already be stopped
        }
        currentAudioSourceRef.current = null
      }
      // Close AudioContext
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close()
        audioContextRef.current = null
      }
    }
  }, [isOpen])

  // Initialize TTS when voice is enabled
  useEffect(() => {
    if (isOpen && voiceEnabled && !ttsInitialized) {
      initializeTTS()
    }
    // Stop audio if voice is disabled
    if (!voiceEnabled && currentAudioSourceRef.current) {
      try {
        currentAudioSourceRef.current.stop()
      } catch (e) {
        // Audio might already be stopped
      }
      currentAudioSourceRef.current = null
      setAudioPlaying(false)
    }
  }, [voiceEnabled, isOpen, ttsInitialized])

  // Update input when STT transcription changes - accumulate text with space continuation
  useEffect(() => {
    if (sttTranscription) {
      setInputText(prevText => {
        if (!prevText) return sttTranscription
        // Add space for continuation
        return prevText + ' ' + sttTranscription
      })
    }
  }, [sttTranscription])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [messages])


  const initializeChat = async () => {
    setStartTime(new Date())
    try {
      const response = await api.getDiaryGreeting()
      if (response.success && response.data) {
        // Ensure we extract the actual string content
        const greetingText = typeof response.data === 'string' ? response.data : 
                           (response.data as any)?.data || 
                           String(response.data)
        
        const greetingMessage: ChatMessage = {
          id: messageIdCounter.current++,
          role: 'assistant',
          content: greetingText,
          timestamp: new Date()
        }
        setMessages([greetingMessage])
        
        // Play greeting if voice is enabled
        if (voiceEnabled && ttsInitialized) {
          playAudioForMessage(greetingText)
        }
      }
    } catch (error) {
      console.error('Failed to get greeting:', error)
      // Fallback greeting
      const fallbackGreeting: ChatMessage = {
        id: messageIdCounter.current++,
        role: 'assistant',
        content: "Hi! I'm Echo, your diary companion. You can type or use the voice button to talk with me. What's on your mind?",
        timestamp: new Date()
      }
      setMessages([fallbackGreeting])
      
      // Play fallback greeting if voice is enabled
      if (voiceEnabled && ttsInitialized) {
        playAudioForMessage(fallbackGreeting.content)
      }
    }
  }

  const initializeTTS = async () => {
    try {
      const response = await api.initializeTTS()
      if (response.success) {
        setTtsInitialized(true)
        console.log('TTS initialized successfully')
      }
    } catch (error) {
      console.error('Failed to initialize TTS:', error)
      // Don't show error to user, just disable TTS silently
    }
  }

  const initializeAudioContext = () => {
    if (!audioContextRef.current) {
      try {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
        
        // Resume AudioContext if it's suspended (required by some browsers)
        if (audioContextRef.current.state === 'suspended') {
          audioContextRef.current.resume()
        }
      } catch (error) {
        console.error('Failed to create AudioContext:', error)
        return false
      }
    }
    return true
  }

  const stripTTSProblematicChars = (text: string): string => {
    // Remove markdown emphasis (*, **)
    let cleanText = text.replace(/\*+/g, '')
    
    // Remove emojis (common Unicode ranges)
    cleanText = cleanText
      // Emoticons (😀-😿)
      .replace(/[\u{1F600}-\u{1F64F}]/gu, '')
      // Symbols & pictographs (🌀-🗿)
      .replace(/[\u{1F300}-\u{1F5FF}]/gu, '')
      // Transport & map symbols (🚀-🛿)
      .replace(/[\u{1F680}-\u{1F6FF}]/gu, '')
      // Supplemental symbols (🤀-🧿)
      .replace(/[\u{1F900}-\u{1F9FF}]/gu, '')
      // Extended pictographs (🪀-🫿)
      .replace(/[\u{1FA70}-\u{1FAFF}]/gu, '')
      // Miscellaneous symbols (☀-⛿)
      .replace(/[\u{2600}-\u{26FF}]/gu, '')
      // Dingbats (✀-➿)
      .replace(/[\u{2700}-\u{27BF}]/gu, '')
    
    // Clean up extra whitespace that might result from removals
    cleanText = cleanText.replace(/\s+/g, ' ').trim()
    
    return cleanText
  }

  const playAudioForMessage = async (text: string) => {
    if (!voiceEnabled || !ttsInitialized || audioPlaying) return
    
    try {
      setAudioPlaying(true)
      
      // Apply second-level stripping: Remove TTS-problematic characters when voice is ON
      const ttsText = stripTTSProblematicChars(text)
      
      // Initialize AudioContext if needed
      if (!initializeAudioContext()) {
        // Fallback to HTML audio
        await playAudioFallback(ttsText)
        return
      }
      
      // Synthesize speech (non-streaming for natural voice resonance)
      const audioBlob = await api.synthesizeSpeech(ttsText, false)
      const arrayBuffer = await audioBlob.arrayBuffer()
      
      // Decode audio data using AudioContext
      const audioBuffer = await audioContextRef.current!.decodeAudioData(arrayBuffer)
      
      // Create and configure audio source
      const source = audioContextRef.current!.createBufferSource()
      source.buffer = audioBuffer
      source.connect(audioContextRef.current!.destination)
      
      // Handle playback end
      source.onended = () => {
        setAudioPlaying(false)
        currentAudioSourceRef.current = null
      }
      
      // Store reference and start playback
      currentAudioSourceRef.current = source
      source.start(0)
      
    } catch (error) {
      console.error('AudioContext playback failed, trying fallback:', error)
      // Fallback to HTML audio (also strip problematic chars)
      const ttsText = stripTTSProblematicChars(text)
      await playAudioFallback(ttsText)
    }
  }

  const playAudioFallback = async (text: string) => {
    try {
      // Note: text should already be cleaned by caller
      // Synthesize speech (non-streaming for natural voice resonance)
      const audioBlob = await api.synthesizeSpeech(text, false)
      const audioUrl = URL.createObjectURL(audioBlob)
      
      // Create and play audio using HTML Audio
      const audio = new Audio(audioUrl)
      audio.onended = () => {
        setAudioPlaying(false)
        URL.revokeObjectURL(audioUrl)
      }
      audio.onerror = () => {
        setAudioPlaying(false)
        URL.revokeObjectURL(audioUrl)
        console.error('HTML Audio playback failed')
      }
      
      await audio.play()
    } catch (error) {
      console.error('All audio playback methods failed:', error)
      setAudioPlaying(false)
    }
  }



  const handleStartRecording = () => {
    startRecording()
  }

  const handleStopRecording = () => {
    stopRecording()
  }

  const handleSendMessage = async () => {
    if (!inputText.trim() || isProcessing) return

    const userMessage: ChatMessage = {
      id: messageIdCounter.current++,
      role: 'user',
      content: inputText.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputText('')
    setIsProcessing(true)

    // Get processing feedback
    try {
      const feedbackResponse = await api.getDiarySearchFeedback()
      if (feedbackResponse.success && feedbackResponse.data) {
        const feedbackText = typeof feedbackResponse.data === 'string' ? feedbackResponse.data : 
                           (feedbackResponse.data as any)?.message || 
                           String(feedbackResponse.data)
        setProcessingMessage(feedbackText)
      }
    } catch (error) {
      setProcessingMessage('Processing...')
    }

    // Send message to AI
    try {
      const conversationHistory = messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }))

      console.log('About to send diary chat message:', userMessage.content)
      const response = await api.sendDiaryChatMessage(
        userMessage.content,
        conversationHistory
      )
      
      console.log('Raw API response received:', response)

      if (response.success && response.data) {
        console.log('Response is successful, processing...')
        // Extract chat data from nested response structure
        const chatData = response.data.data || response.data
        
        // Check if tool calls were made
        const hasToolCalls = chatData.tool_calls_made?.length > 0
        setIsToolCall(hasToolCalls)
        
        // Update search queries
        if (chatData.search_queries_used?.length > 0) {
          setSearchQueries(prev => [...prev, ...chatData.search_queries_used])
        }

        // Debug: log the response data
        console.log('Full response:', response)
        console.log('Response data:', response.data)
        console.log('Nested response data:', response.data.data)
        console.log('Response text field:', chatData.response)
        
        // Extract the actual response text from the nested structure
        const responseText = typeof chatData.response === 'string' ? chatData.response : 
                           String(chatData.response || 'No response received')

        // Create AI response message
        const aiMessage: ChatMessage = {
          id: messageIdCounter.current++,
          role: 'assistant',
          content: responseText,
          timestamp: new Date(),
          isStreaming: true // We'll simulate streaming
        }

        setMessages(prev => [...prev, aiMessage])
        
        // Play audio after message is added if voice is enabled
        // We'll let the typewriter animation handle the display
        if (voiceEnabled && ttsInitialized) {
          // Delay audio to let typewriter finish
          setTimeout(() => {
            playAudioForMessage(responseText)
          }, responseText.length * 25) // Match typewriter speed
        }

      } else {
        console.error('Response not successful or missing data:', response)
        // Add fallback AI message for failed responses
        const errorMessage: ChatMessage = {
          id: messageIdCounter.current++,
          role: 'assistant',
          content: 'I apologize, but I encountered an issue processing your message. Please try again.',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, errorMessage])
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      safeToast({
        title: 'Failed to send message',
        description: 'Please check your connection and try again'
      })
    } finally {
      setIsProcessing(false)
      setProcessingMessage('')
      setIsToolCall(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const getTranscription = () => {
    return messages.map(msg => {
      const speaker = msg.role === 'user' ? 'You' : 'Echo'
      const time = msg.timestamp.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
      return `[${time}] ${speaker}: ${msg.content}`
    }).join('\n')
  }

  const getDuration = () => {
    if (!startTime) return 0
    return Math.floor((new Date().getTime() - startTime.getTime()) / 1000)
  }

  const handleEndChat = () => {
    const transcription = getTranscription()
    const duration = getDuration()
    const messageCount = messages.length
    onEndChat(transcription, duration, messageCount, searchQueries)
  }

  const handleClose = () => {
    const transcription = getTranscription()
    const duration = getDuration()
    const messageCount = messages.length
    onClose(transcription, duration, messageCount, searchQueries)
  }

  if (!isOpen) return null

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={handleClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-card/90 backdrop-blur-xl border border-border/50 rounded-2xl shadow-2xl max-w-5xl w-full h-[90vh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 pt-6 pb-4 border-b border-border/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <Send className="h-4 w-4 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-white">Talk to Echo</h2>
                <p className="text-sm text-gray-400">Your AI journal companion</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Label htmlFor="modal-voice-toggle" className="text-sm text-gray-300">
                  Voice
                </Label>
                <Switch
                  id="modal-voice-toggle"
                  checked={voiceEnabled}
                  onCheckedChange={onVoiceToggle}
                />
                <Volume2 className={`h-4 w-4 ${voiceEnabled ? 'text-primary' : 'text-muted-foreground'}`} />
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleEndChat}
                className="h-10 w-10 p-0 text-blue-300 drop-shadow-[0_0_4px_rgba(147,197,253,0.6)] hover:bg-muted/50 hover:text-white hover:drop-shadow-[0_0_6px_rgba(255,255,255,0.6)]"
                title="Close"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </div>

        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Messages Area */}
          <div className="flex-1 px-6 py-4 overflow-y-auto space-y-4" ref={scrollAreaRef}>
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-start' : 'justify-end'}`}
                >
                  <div
                    className={`max-w-[70%] px-4 py-2 rounded-lg ${
                      message.role === 'user'
                        ? 'bg-gradient-to-br from-blue-500/20 to-cyan-500/20 border border-blue-500/30 text-white'
                        : 'bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30 text-white'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">
                      {message.role === 'assistant' && message.isStreaming ? (
                        <TypewriterText 
                          text={message.content} 
                          isActive={true}
                          onComplete={() => {
                            setMessages(prev => prev.map(msg => 
                              msg.id === message.id 
                                ? { ...msg, isStreaming: false }
                                : msg
                            ))
                          }}
                        />
                      ) : (
                        message.content
                      )}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Processing Indicator */}
          {isProcessing && (
            <div className="px-6 py-2 border-t">
              <div className={`flex items-center gap-2 text-sm ${isToolCall ? 'text-green-600 dark:text-green-400' : 'text-muted-foreground'}`}>
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>{typeof processingMessage === 'string' ? processingMessage : 'Processing...'}</span>
                <span className="animate-pulse">...</span>
              </div>
            </div>
          )}

          {/* Audio Playing Indicator */}
          {audioPlaying && voiceEnabled && (
            <div className="px-6 py-2 border-t">
              <div className="flex items-center gap-2 text-sm text-primary">
                <Volume2 className="h-3 w-3 animate-pulse" />
                <span>Speaking...</span>
              </div>
            </div>
          )}

          {/* Input Area */}
          <div className="border-t px-6 py-4">
            <div className="flex items-center gap-2">
              <Input
                ref={inputRef}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message or use the mic..."
                disabled={isProcessing || isRecording || isTranscribing}
                className="flex-1 h-12 px-4"
              />
              <button
                onClick={isRecording ? handleStopRecording : handleStartRecording}
                disabled={isProcessing || isTranscribing}
                className={`relative overflow-hidden group p-2.5 rounded-lg font-medium shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer inline-flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed ${
                  isRecording 
                    ? 'bg-red-500/20 border border-red-500/30 text-red-400 hover:bg-red-500/30'
                    : 'bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30 text-purple-300 hover:from-purple-500/30 hover:to-pink-500/30'
                }`}
              >
                <div className={`absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 ${
                  isRecording 
                    ? 'bg-gradient-to-r from-red-500/10 to-red-600/10'
                    : 'bg-gradient-to-r from-purple-500/10 to-pink-500/10'
                }`} />
                <span className="relative z-10">
                  {isRecording ? (
                    <MicOff className="h-4 w-4" />
                  ) : (
                    <Mic className="h-4 w-4" />
                  )}
                </span>
              </button>
              <button
                onClick={handleSendMessage}
                disabled={!inputText.trim() || isProcessing}
                className="relative overflow-hidden group px-4 py-2.5 rounded-lg font-medium shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all duration-300 cursor-pointer inline-flex items-center justify-center bg-primary/20 border border-primary/40 text-primary hover:bg-primary/30 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-secondary/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <span className="relative z-10">
                  <Send className="h-4 w-4" />
                </span>
              </button>
            </div>
            {(isRecording || isTranscribing) && (
              <p className="text-xs text-muted-foreground mt-2">
                {isRecording ? 'Recording... Click to stop' : 'Transcribing...'}
              </p>
            )}
            {sttError && (
              <p className="text-xs text-destructive mt-2">{sttError}</p>
            )}
          </div>

        </div>
      </motion.div>
    </motion.div>
  )
}

export default ChatModal
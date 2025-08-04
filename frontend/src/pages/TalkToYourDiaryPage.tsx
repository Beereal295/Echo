import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Mic, MessageSquare, Trash2, Volume2 } from 'lucide-react'
import { api } from '@/lib/api'
import { format } from 'date-fns'
import { motion, AnimatePresence } from 'framer-motion'
import { useToast } from '@/components/ui/use-toast'
import ChatModal from '@/components/ChatModal'
import SaveDiscardModal from '@/components/SaveDiscardModal'

// Types
interface Conversation {
  id: number
  timestamp: string
  duration: number
  transcription: string
  conversation_type: string
  message_count: number
  search_queries_used: string[]
  created_at: string
  updated_at?: string
}

interface ConversationPreview {
  conversation: Conversation
  isExpanded: boolean
}

function TalkToYourDiaryPage() {
  const [voiceEnabled, setVoiceEnabled] = useState(true)
  const [conversations, setConversations] = useState<ConversationPreview[]>([])
  const [isChatModalOpen, setIsChatModalOpen] = useState(false)
  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false)
  const [currentTranscription, setCurrentTranscription] = useState('')
  const [conversationToSave, setConversationToSave] = useState<{
    transcription: string
    duration: number
    messageCount: number
    searchQueries: string[]
  } | null>(null)
  const [loading, setLoading] = useState(false)
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

  // Load voice preference and conversations on mount
  useEffect(() => {
    loadVoicePreference()
    loadConversations()
  }, [])


  // Save voice preference whenever it changes
  useEffect(() => {
    saveVoicePreference()
  }, [voiceEnabled])

  const loadVoicePreference = async () => {
    try {
      const response = await api.getPreferences()
      if (response.success && response.data?.preferences) {
        const voicePref = response.data.preferences.find(p => p.key === 'voice_enabled')
        if (voicePref) {
          setVoiceEnabled(voicePref.value === 'true')
        }
      }
    } catch (error) {
      console.error('Failed to load voice preference:', error)
    }
  }

  const saveVoicePreference = async () => {
    try {
      await api.updatePreference('voice_enabled', voiceEnabled.toString())
    } catch (error) {
      console.error('Failed to save voice preference:', error)
    }
  }

  const loadConversations = async () => {
    setLoading(true)
    try {
      const response = await api.getConversations()
      if (response.success && response.data && response.data.conversations) {
        const conversationPreviews = response.data.conversations.map(conv => ({
          conversation: conv,
          isExpanded: false
        }))
        setConversations(conversationPreviews)
      } else {
        // No conversations yet or empty response
        setConversations([])
      }
    } catch (error) {
      console.error('Failed to load conversations:', error)
      setConversations([])
      safeToast({
        title: 'Failed to load conversations',
        description: 'Please check your connection and try again'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleStartChat = () => {
    setIsChatModalOpen(true)
  }

  const handleChatEnd = (transcription: string, duration: number, messageCount: number, searchQueries: string[]) => {
    setCurrentTranscription(transcription)
    setConversationToSave({
      transcription,
      duration,
      messageCount,
      searchQueries
    })
    setIsChatModalOpen(false)
    setIsSaveModalOpen(true)
  }

  const handleChatClose = async (transcription: string, duration: number, messageCount: number, searchQueries: string[]) => {
    // Auto-save on X button close
    try {
      await api.createConversation({
        transcription,
        conversation_type: 'chat',
        duration,
        message_count: messageCount,
        search_queries_used: searchQueries
      })
      safeToast({
        title: 'Conversation saved',
        description: 'Your chat with Echo has been saved successfully'
      })
      loadConversations()
    } catch (error) {
      console.error('Failed to save conversation:', error)
      safeToast({
        title: 'Failed to save conversation',
        description: 'Please try again'
      })
    }
    setIsChatModalOpen(false)
  }

  const handleSaveConversation = async () => {
    if (!conversationToSave) return

    try {
      await api.createConversation({
        transcription: conversationToSave.transcription,
        conversation_type: 'chat',
        duration: conversationToSave.duration,
        message_count: conversationToSave.messageCount,
        search_queries_used: conversationToSave.searchQueries
      })
      safeToast({
        title: 'Conversation saved',
        description: 'Your chat with Echo has been saved successfully'
      })
      loadConversations()
      setIsSaveModalOpen(false)
      setConversationToSave(null)
    } catch (error) {
      console.error('Failed to save conversation:', error)
      safeToast({
        title: 'Failed to save conversation',
        description: 'Please try again'
      })
    }
  }

  const handleDiscardConversation = () => {
    setIsSaveModalOpen(false)
    setConversationToSave(null)
    setCurrentTranscription('')
  }

  const handleDeleteConversation = async (id: number) => {
    try {
      await api.deleteConversation(id)
      safeToast({
        title: 'Conversation deleted',
        description: 'The conversation has been removed successfully'
      })
      loadConversations()
    } catch (error) {
      console.error('Failed to delete conversation:', error)
      safeToast({
        title: 'Failed to delete conversation',
        description: 'Please try again'
      })
    }
  }

  const toggleConversationExpand = (index: number) => {
    setConversations(prev => prev.map((conv, i) => 
      i === index ? { ...conv, isExpanded: !conv.isExpanded } : conv
    ))
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getConversationPreview = (transcription: string) => {
    const lines = transcription.split('\n')
    const preview = lines.slice(0, 3).join('\n')
    return preview.length > 150 ? preview.substring(0, 150) + '...' : preview
  }

  return (
    <div className="max-w-7xl mx-auto p-8">
      <h2 className="text-2xl font-bold mb-6">Talk to Your Diary</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Card - Talk to Echo */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Card className="bg-card/50 backdrop-blur-sm border-border/50 h-[600px] flex flex-col">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                  <MessageSquare className="h-4 w-4 text-white" />
                </div>
                <div className="min-w-0">
                  <CardTitle className="text-lg text-white">Talk to Echo</CardTitle>
                  <p className="text-gray-400 text-sm">
                    Your AI diary companion
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col items-center justify-center gap-6">
              {/* Animated Echo Icon */}
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="relative"
              >
                <motion.div
                  animate={{ 
                    scale: [1, 1.05, 1]
                  }}
                  transition={{ 
                    duration: 3, 
                    repeat: Infinity, 
                    ease: "easeInOut" 
                  }}
                  className="w-20 h-20 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center border border-primary/30"
                >
                  <Mic className="h-8 w-8 text-primary" />
                </motion.div>
                {/* Breathing glow effect */}
                <motion.div
                  animate={{ 
                    opacity: [0.2, 0.8, 0.2],
                    scale: [1, 1.2, 1]
                  }}
                  transition={{ 
                    duration: 4, 
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                  className="absolute inset-0 rounded-full bg-primary/20 blur-xl"
                />
                {/* Secondary outer glow */}
                <motion.div
                  animate={{ 
                    opacity: [0.1, 0.4, 0.1],
                    scale: [1.2, 1.5, 1.2]
                  }}
                  transition={{ 
                    duration: 5, 
                    repeat: Infinity,
                    ease: "easeInOut",
                    delay: 1
                  }}
                  className="absolute inset-0 rounded-full bg-primary/10 blur-2xl"
                />
              </motion.div>
              
              <div className="text-center space-y-4">
                <motion.p 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                  className="text-gray-400 max-w-sm"
                >
                  Share your thoughts, explore memories, and reflect with your personal AI companion.
                </motion.p>
                
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 }}
                  className="flex items-center justify-center gap-3"
                >
                  <Label htmlFor="voice-toggle" className="text-sm font-medium text-gray-300">
                    Voice responses
                  </Label>
                  <Switch
                    id="voice-toggle"
                    checked={voiceEnabled}
                    onCheckedChange={setVoiceEnabled}
                  />
                  <Volume2 className={`h-4 w-4 ${voiceEnabled ? 'text-primary' : 'text-muted-foreground'}`} />
                </motion.div>
              </div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8 }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <button
                  onClick={handleStartChat}
                  className="relative overflow-hidden group px-8 py-3 rounded-lg font-medium shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer inline-flex items-center justify-center bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 gap-3"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-secondary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <span className="relative z-10 flex items-center font-medium">
                    <Mic className="h-5 w-5 mr-2" />
                    Start Conversation
                  </span>
                </button>
              </motion.div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Right Card - Saved Conversations */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <Card className="bg-card/50 backdrop-blur-sm border-border/50 h-[600px] flex flex-col">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-green-500 to-teal-600 flex items-center justify-center flex-shrink-0">
                  <MessageSquare className="h-4 w-4 text-white" />
                </div>
                <div className="min-w-0">
                  <CardTitle className="text-lg text-white">Conversation History</CardTitle>
                  <p className="text-gray-400 text-sm">
                    Your saved chats with Echo
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent className="flex-1 overflow-hidden p-4">
              {loading ? (
                <div className="flex items-center justify-center h-full">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full"
                  />
                </div>
              ) : conversations.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: "spring", delay: 0.2 }}
                    className="w-16 h-16 rounded-full bg-muted/20 flex items-center justify-center"
                  >
                    <MessageSquare className="h-8 w-8 text-muted-foreground" />
                  </motion.div>
                  <div>
                    <p className="text-gray-400 font-medium">No conversations yet</p>
                    <p className="text-gray-500 text-sm mt-1">
                      Start your first chat with Echo to see it here
                    </p>
                  </div>
                </div>
              ) : (
                <div className="h-full overflow-y-auto pr-2 space-y-2">
                  <AnimatePresence>
                    {conversations.map((conv, index) => (
                      <motion.div
                        key={conv.conversation.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ delay: index * 0.05 }}
                        whileHover={{ y: -2 }}
                      >
                        <Card 
                          className={`cursor-pointer transition-all duration-200 hover:shadow-md ${
                            conv.isExpanded ? 'ring-2 ring-primary/50 bg-primary/5' : 'hover:bg-muted/30'
                          }`}
                          onClick={() => toggleConversationExpand(index)}
                        >
                          <CardContent className="p-3">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <Badge variant="secondary" className="text-xs px-2 py-0.5">
                                  Chat
                                </Badge>
                                <span className="text-xs text-gray-400">
                                  {format(new Date(conv.conversation.timestamp), 'MMM d, h:mm a')}
                                </span>
                              </div>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6 hover:bg-destructive/20 hover:text-destructive"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleDeleteConversation(conv.conversation.id)
                                }}
                              >
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            </div>
                            
                            <p className="text-sm text-gray-300 mb-2 line-clamp-2">
                              {conv.isExpanded 
                                ? conv.conversation.transcription
                                : getConversationPreview(conv.conversation.transcription)
                              }
                            </p>
                            
                            <div className="flex items-center gap-3 text-xs text-gray-500">
                              <span className="flex items-center gap-1">
                                ⏱️ {formatDuration(conv.conversation.duration)}
                              </span>
                              <span className="flex items-center gap-1">
                                💬 {conv.conversation.message_count}
                              </span>
                              {conv.conversation.search_queries_used.length > 0 && (
                                <span className="flex items-center gap-1">
                                  🔍 {conv.conversation.search_queries_used.length}
                                </span>
                              )}
                            </div>
                          </CardContent>
                        </Card>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Chat Modal */}
      <ChatModal
        isOpen={isChatModalOpen}
        onClose={handleChatClose}
        onEndChat={handleChatEnd}
        voiceEnabled={voiceEnabled}
        onVoiceToggle={setVoiceEnabled}
      />

      {/* Save/Discard Modal */}
      <SaveDiscardModal
        isOpen={isSaveModalOpen}
        onClose={() => setIsSaveModalOpen(false)}
        onSave={handleSaveConversation}
        onDiscard={handleDiscardConversation}
        transcription={conversationToSave?.transcription || ''}
        duration={conversationToSave?.duration || 0}
        messageCount={conversationToSave?.messageCount || 0}
      />
    </div>
  )
}

export default TalkToYourDiaryPage
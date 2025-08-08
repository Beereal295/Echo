import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence, useMotionValue, useTransform, PanInfo } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Brain, Heart, ThumbsUp, ThumbsDown, RotateCcw, Loader2, Sparkles, Users, Target } from 'lucide-react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'

interface Memory {
  id: number
  content: string
  memory_type: string
  base_importance_score: number
  llm_importance_score?: number
  user_score_adjustment: number
  final_importance_score: number
  user_rated: number
  score_source: string
  effective_score_data?: any
  created_at: string
  last_accessed_at?: string
  access_count: number
}

function MemoriesPage() {
  const [memories, setMemories] = useState<Memory[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [isRating, setIsRating] = useState(false)
  const [showConfirmation, setShowConfirmation] = useState(false)
  const [showFirstTimeModal, setShowFirstTimeModal] = useState(false)
  const [lastAction, setLastAction] = useState<{ type: 'relevant' | 'irrelevant', memoryId: number } | null>(null)
  const [stats, setStats] = useState<any>(null)
  const { toast } = useToast()

  // Check if user has seen the tutorial
  const [hasSeenTutorial, setHasSeenTutorial] = useState(() => {
    return localStorage.getItem('memory-tutorial-seen') === 'true'
  })

  useEffect(() => {
    // Show tutorial modal on first visit
    if (!hasSeenTutorial && memories.length > 0) {
      setShowFirstTimeModal(true)
    }
  }, [memories.length, hasSeenTutorial])

  // Reset tutorial state when component unmounts (user navigates away)
  useEffect(() => {
    return () => {
      if (hasSeenTutorial) {
        localStorage.removeItem('memory-tutorial-seen')
      }
    }
  }, [])

  // Motion values for drag with increased threshold
  const x = useMotionValue(0)
  const y = useMotionValue(0)
  const rotate = useTransform(x, [-300, 300], [-25, 25])
  const opacity = useTransform(x, [-300, -150, 0, 150, 300], [0, 0.5, 1, 0.5, 0])
  
  // Swipe threshold - increased for less reactivity
  const SWIPE_THRESHOLD = 120

  useEffect(() => {
    loadMemories()
    loadStats()
  }, [])

  const loadMemories = async () => {
    try {
      setLoading(true)
      const response = await api.getUnratedMemories(20) // Load more for stack
      if (response.success && response.data) {
        setMemories(response.data)
        setCurrentIndex(0)
      } else {
        toast({
          title: "Error",
          description: "Failed to load memories",
          variant: "destructive"
        })
      }
    } catch (error) {
      console.error('Failed to load memories:', error)
      toast({
        title: "Error", 
        description: "Network error while loading memories",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const response = await api.getMemoryStats()
      if (response.success && response.data) {
        setStats(response.data)
      }
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }

  const rateMemory = async (memoryId: number, isRelevant: boolean) => {
    if (isRating) return

    setIsRating(true)
    try {
      const adjustment = isRelevant ? 2 : -3 // Relevant: +2, Irrelevant: -3
      const response = await api.rateMemory(memoryId, adjustment)
      
      if (response.success) {
        setLastAction({
          type: isRelevant ? 'relevant' : 'irrelevant',
          memoryId
        })
        setShowConfirmation(true)
        
        // Move to next memory after short delay
        setTimeout(() => {
          setCurrentIndex(prev => prev + 1)
          setShowConfirmation(false)
        }, 1500)

        // Reload stats
        loadStats()
      } else {
        toast({
          title: "Error",
          description: response.error || "Failed to rate memory",
          variant: "destructive"
        })
      }
    } catch (error) {
      console.error('Failed to rate memory:', error)
      toast({
        title: "Error",
        description: "Network error while rating memory",
        variant: "destructive"
      })
    } finally {
      setIsRating(false)
    }
  }

  const handleDragEnd = (event: any, info: PanInfo) => {
    const { offset, velocity } = info
    
    // Determine swipe direction and threshold
    const swipeVelocityThreshold = 500

    if (Math.abs(offset.x) > SWIPE_THRESHOLD || Math.abs(velocity.x) > swipeVelocityThreshold) {
      const currentMemory = memories[currentIndex]
      if (currentMemory) {
        // Show confirmation modal on first swipe if tutorial not seen
        if (!hasSeenTutorial) {
          setShowFirstTimeModal(true)
          x.set(0) // Reset position
          y.set(0)
          return
        }
        
        if (offset.x > 0) {
          // Swipe right - relevant (+2)
          rateMemory(currentMemory.id, true)
        } else {
          // Swipe left - irrelevant (-3)
          rateMemory(currentMemory.id, false)
        }
      }
    } else {
      // Snap back to center
      x.set(0)
      y.set(0)
    }
  }

  const handleTutorialComplete = () => {
    setShowFirstTimeModal(false)
    setHasSeenTutorial(true)
    localStorage.setItem('memory-tutorial-seen', 'true')
  }

  const handleButtonRate = (isRelevant: boolean) => {
    const currentMemory = memories[currentIndex]
    if (currentMemory) {
      if (!hasSeenTutorial) {
        setShowFirstTimeModal(true)
        return
      }
      rateMemory(currentMemory.id, isRelevant)
    }
  }

  const getMemoryTypeIcon = (type: string) => {
    switch (type) {
      case 'factual':
        return <Brain className="w-4 h-4" />
      case 'preference':
        return <Heart className="w-4 h-4" />
      case 'relational':
        return <Users className="w-4 h-4" />
      case 'behavioral':
        return <Target className="w-4 h-4" />
      default:
        return <Sparkles className="w-4 h-4" />
    }
  }

  const getMemoryTypeColor = (type: string) => {
    switch (type) {
      case 'factual':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
      case 'preference':
        return 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200'
      case 'relational':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'behavioral':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
    }
  }

  const formatMemoryType = (type: string) => {
    return type.charAt(0).toUpperCase() + type.slice(1)
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
          <p className="text-muted-foreground">Loading your memories...</p>
        </div>
      </div>
    )
  }

  if (memories.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="text-center max-w-md">
          <Sparkles className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
          <h2 className="text-2xl font-semibold mb-2">No Memories to Review</h2>
          <p className="text-muted-foreground mb-4">
            All your memories have been rated! Come back later as Echo learns more about you through your journal entries and conversations.
          </p>
          <Button onClick={loadMemories} variant="outline">
            Check Again
          </Button>
        </div>
      </div>
    )
  }

  const currentMemory = memories[currentIndex]
  const isComplete = currentIndex >= memories.length

  if (isComplete) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="text-center max-w-md">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="w-16 h-16 mx-auto mb-4 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center"
          >
            <ThumbsUp className="w-8 h-8 text-green-600 dark:text-green-400" />
          </motion.div>
          <h2 className="text-2xl font-semibold mb-2">All Done!</h2>
          <p className="text-muted-foreground mb-4">
            You've reviewed all available memories. Thank you for helping Echo understand what's important to you!
          </p>
          <Button onClick={loadMemories} variant="outline">
            <RotateCcw className="w-4 h-4 mr-2" />
            Check for New Memories
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Memory Review</h1>
        <p className="text-muted-foreground">
          Help Echo understand what's important to you by rating your memories
        </p>
        
        {/* Stats */}
        {stats && (
          <div className="flex gap-4 mt-4">
            <Badge variant="outline" className="flex items-center gap-2">
              <Brain className="w-3 h-3" />
              {stats.unrated_memories} unrated
            </Badge>
            <Badge variant="outline" className="flex items-center gap-2">
              <ThumbsUp className="w-3 h-3" />
              {stats.rated_memories} rated
            </Badge>
          </div>
        )}
      </div>

      {/* Progress */}
      <div className="mb-8">
        <div className="flex justify-between text-sm text-muted-foreground mb-2">
          <span>Progress</span>
          <span>{currentIndex + 1} / {memories.length}</span>
        </div>
        <div className="w-full bg-muted rounded-full h-2">
          <motion.div
            className="bg-primary h-2 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${((currentIndex + 1) / memories.length) * 100}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      </div>

      {/* Card Stack Container */}
      <div className="flex-1 flex items-center justify-center relative">
        <AnimatePresence>
          {showConfirmation && lastAction && (
            <motion.div
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
              className="absolute inset-0 flex items-center justify-center z-50 bg-background/80 backdrop-blur-sm rounded-xl"
            >
              <motion.div
                initial={{ y: 20 }}
                animate={{ y: 0 }}
                className={`p-8 rounded-lg border ${
                  lastAction.type === 'relevant' 
                    ? 'bg-green-50 border-green-200 dark:bg-green-950 dark:border-green-800' 
                    : 'bg-red-50 border-red-200 dark:bg-red-950 dark:border-red-800'
                }`}
              >
                <div className="text-center">
                  <div className={`w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center ${
                    lastAction.type === 'relevant' 
                      ? 'bg-green-100 dark:bg-green-900' 
                      : 'bg-red-100 dark:bg-red-900'
                  }`}>
                    {lastAction.type === 'relevant' ? (
                      <ThumbsUp className="w-8 h-8 text-green-600 dark:text-green-400" />
                    ) : (
                      <ThumbsDown className="w-8 h-8 text-red-600 dark:text-red-400" />
                    )}
                  </div>
                  <h3 className="text-xl font-semibold mb-2">
                    {lastAction.type === 'relevant' ? 'Marked as Relevant' : 'Marked as Irrelevant'}
                  </h3>
                  <p className="text-muted-foreground">
                    {lastAction.type === 'relevant' 
                      ? 'This memory will be prioritized by Echo'
                      : 'This memory will be deprioritized by Echo'
                    }
                  </p>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Card Stack */}
        <div className="relative w-full max-w-lg h-96">
          {memories.slice(currentIndex, currentIndex + 3).map((memory, index) => {
            const isTopCard = index === 0
            const zIndex = 3 - index
            const scale = 1 - index * 0.08  // More pronounced scaling
            const yOffset = index * 16      // More visible vertical offset
            const xOffset = index * 8       // Add horizontal offset for stack effect

            return (
              <motion.div
                key={memory.id}
                className="absolute inset-0"
                style={{
                  zIndex,
                  scale: isTopCard ? undefined : scale,
                  y: isTopCard ? y : yOffset,
                  x: isTopCard ? x : xOffset,
                  rotate: isTopCard ? rotate : 0,
                  opacity: isTopCard ? opacity : Math.max(0.7, 1 - index * 0.25)
                }}
                drag={isTopCard ? "x" : false}
                dragConstraints={{ left: 0, right: 0 }}
                onDragEnd={isTopCard ? handleDragEnd : undefined}
                animate={isTopCard ? undefined : { scale, y: yOffset, x: xOffset }}
                transition={{ duration: 0.2 }}
              >
                <Card className={`w-full h-full cursor-pointer transition-all duration-300 overflow-hidden group relative ${
                  isTopCard 
                    ? 'bg-card border-border shadow-xl hover:shadow-2xl z-10' 
                    : 'bg-card/80 border-border/70 shadow-lg'
                }`}>
                  {/* Shimmer effect only on top card */}
                  {isTopCard && (
                    <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/10 to-transparent group-hover:translate-x-full transition-transform duration-700" />
                  )}
                  <CardHeader className="pb-4 relative">
                    <div className="flex items-start justify-between">
                      <Badge 
                        variant="secondary" 
                        className={`flex items-center gap-1 ${getMemoryTypeColor(memory.memory_type)}`}
                      >
                        {getMemoryTypeIcon(memory.memory_type)}
                        {formatMemoryType(memory.memory_type)}
                      </Badge>
                      <div className="text-right">
                        <div className="text-sm text-muted-foreground">Score</div>
                        <div className="text-lg font-semibold">
                          {memory.final_importance_score.toFixed(1)}/10
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  
                  <CardContent className="flex-1 flex flex-col justify-between relative">
                    <div>
                      <p className="text-base leading-relaxed mb-4">
                        {memory.content}
                      </p>
                    </div>
                    
                    <div className="space-y-3">
                      {/* Score details */}
                      <div className="text-xs text-muted-foreground">
                        <div className="flex justify-between">
                          <span>Source:</span>
                          <span className="capitalize">{memory.score_source}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Accessed:</span>
                          <span>{memory.access_count} times</span>
                        </div>
                      </div>
                      
                      {/* Instructions (only show on top card) */}
                      {isTopCard && (
                        <div className="text-center text-sm text-muted-foreground border-t pt-3">
                          <p className="mb-2">Swipe or click to rate</p>
                          <div className="flex justify-center gap-4">
                            <span className="text-red-600">← Irrelevant</span>
                            <span className="text-green-600">Relevant →</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )
          })}
        </div>

        {/* Action Buttons */}
        <div className="absolute bottom-[-80px] left-1/2 transform -translate-x-1/2 flex gap-4">
          <Button
            variant="outline"
            size="lg"
            onClick={() => handleButtonRate(false)}
            disabled={isRating}
            className="bg-red-50 border-red-200 hover:bg-red-100 text-red-700 dark:bg-red-950 dark:border-red-800 dark:hover:bg-red-900 dark:text-red-300"
          >
            {isRating ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <ThumbsDown className="w-5 h-5" />
            )}
            <span className="ml-2">Irrelevant</span>
          </Button>
          
          <Button
            variant="outline"
            size="lg"
            onClick={() => handleButtonRate(true)}
            disabled={isRating}
            className="bg-green-50 border-green-200 hover:bg-green-100 text-green-700 dark:bg-green-950 dark:border-green-800 dark:hover:bg-green-900 dark:text-green-300"
          >
            {isRating ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <ThumbsUp className="w-5 h-5" />
            )}
            <span className="ml-2">Relevant</span>
          </Button>
        </div>
      </div>

      {/* First-time tutorial modal */}
      <AnimatePresence>
        {showFirstTimeModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-card border border-border rounded-lg p-6 max-w-md w-full shadow-xl"
            >
              <div className="text-center">
                <div className="mb-4">
                  <Brain className="w-12 h-12 mx-auto text-primary mb-2" />
                  <h3 className="text-xl font-semibold text-white">Memory Review Tutorial</h3>
                </div>
                
                <div className="text-gray-300 space-y-3 mb-6 text-left">
                  <p className="flex items-center gap-2">
                    <span className="text-green-400">👉</span>
                    <strong>Swipe Right</strong> or click <strong>Relevant</strong> for memories that helped you
                  </p>
                  <p className="flex items-center gap-2">
                    <span className="text-red-400">👈</span>
                    <strong>Swipe Left</strong> or click <strong>Not Relevant</strong> for memories that didn't
                  </p>
                  <p className="text-sm text-gray-400 mt-4 text-center">
                    Your ratings help Echo learn what's important to you!
                  </p>
                </div>

                <Button 
                  onClick={handleTutorialComplete}
                  className="w-full"
                >
                  <Sparkles className="w-4 h-4 mr-2" />
                  Got it! Let's start
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default MemoriesPage
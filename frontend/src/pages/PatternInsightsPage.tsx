import { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import WordCloud from '@/components/WordCloud'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/components/ui/use-toast'
import { api } from '@/lib/api'
import { 
  Diamond, 
  Sparkles, 
  TrendingUp, 
  Calendar, 
  Heart,
  Loader2,
  RefreshCw,
  ChevronRight,
  Clock,
  Hash
} from 'lucide-react'
import { format } from 'date-fns'

interface Pattern {
  id: number
  pattern_type: string
  description: string
  frequency: number
  confidence: number
  first_seen: string
  last_seen: string
  related_entries: number[]
  keywords: string[]
}

interface WordCloudWord {
  text: string
  value: number
}

function PatternInsightsPage() {
  const { toast } = useToast()
  const [patterns, setPatterns] = useState<Pattern[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [selectedPattern, setSelectedPattern] = useState<Pattern | null>(null)
  const [showUnlockAnimation, setShowUnlockAnimation] = useState(false)

  useEffect(() => {
    checkAndLoadPatterns()
  }, [])

  const checkAndLoadPatterns = async () => {
    setLoading(true)
    try {
      // Check if threshold is met
      const thresholdResponse = await api.checkPatternThreshold()
      if (thresholdResponse.success && thresholdResponse.data) {
        if (!thresholdResponse.data.threshold_met) {
          // Show message about needing more entries
          toast({
            title: 'More entries needed',
            description: `You need ${thresholdResponse.data.remaining} more entries to unlock pattern insights.`,
            variant: 'default'
          })
          setLoading(false)
          return
        }
      }

      // Load patterns
      const patternsResponse = await api.getPatterns()
      if (patternsResponse.success && patternsResponse.data) {
        setPatterns(patternsResponse.data.patterns)
        
        // Check if this is the first time viewing patterns
        const hasViewedPatterns = localStorage.getItem('hasViewedPatterns')
        if (!hasViewedPatterns && patternsResponse.data.patterns.length > 0) {
          setShowUnlockAnimation(true)
          localStorage.setItem('hasViewedPatterns', 'true')
        }
      }
    } catch (error) {
      console.error('Failed to load patterns:', error)
      toast({
        title: 'Error loading patterns',
        description: 'Failed to load your pattern insights',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  const refreshPatterns = async () => {
    setRefreshing(true)
    try {
      const response = await api.analyzePatterns()
      if (response.success) {
        toast({
          title: 'Patterns refreshed',
          description: `Found ${response.data?.patterns_found || 0} patterns`,
        })
        await checkAndLoadPatterns()
      }
    } catch (error) {
      console.error('Failed to refresh patterns:', error)
      toast({
        title: 'Error refreshing patterns',
        description: 'Failed to analyze your entries',
        variant: 'destructive'
      })
    } finally {
      setRefreshing(false)
    }
  }

  // Generate word cloud data from all patterns
  const wordCloudData = useMemo(() => {
    const wordFrequency: Record<string, number> = {}
    
    patterns.forEach(pattern => {
      pattern.keywords.forEach(keyword => {
        wordFrequency[keyword] = (wordFrequency[keyword] || 0) + pattern.frequency
      })
    })

    return Object.entries(wordFrequency)
      .map(([text, value]) => ({ text, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 50) // Top 50 words
  }, [patterns])

  // Group patterns by type
  const patternsByType = useMemo(() => {
    const grouped: Record<string, Pattern[]> = {
      topic: [],
      mood: [],
      temporal: [],
      behavior: []
    }
    
    patterns.forEach(pattern => {
      if (grouped[pattern.pattern_type]) {
        grouped[pattern.pattern_type].push(pattern)
      }
    })
    
    return grouped
  }, [patterns])

  const getPatternIcon = (type: string) => {
    switch (type) {
      case 'mood':
        return Heart
      case 'temporal':
        return Calendar
      case 'topic':
        return Hash
      default:
        return TrendingUp
    }
  }

  const getPatternColor = (type: string) => {
    switch (type) {
      case 'mood':
        return 'text-pink-500'
      case 'temporal':
        return 'text-blue-500'
      case 'topic':
        return 'text-purple-500'
      default:
        return 'text-green-500'
    }
  }

  const handleWordClick = (word: any) => {
    // Find patterns containing this keyword
    const relatedPatterns = patterns.filter(p => 
      p.keywords.includes(word.text)
    )
    if (relatedPatterns.length > 0) {
      setSelectedPattern(relatedPatterns[0])
    }
  }

  if (loading) {
    return (
      <div className="h-screen flex flex-col p-4 md:p-6 overflow-hidden">
        <div className="max-w-6xl mx-auto w-full flex flex-col flex-1">
          <div className="mb-4">
            <Skeleton className="h-8 w-48 mb-2" />
            <Skeleton className="h-4 w-64" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Skeleton className="h-96" />
            <Skeleton className="h-96" />
          </div>
        </div>
      </div>
    )
  }

  if (patterns.length === 0) {
    return (
      <div className="h-screen flex flex-col p-4 md:p-6 overflow-hidden">
        <div className="max-w-6xl mx-auto w-full flex flex-col flex-1 items-center justify-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center"
          >
            <Diamond className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">No Patterns Yet</h2>
            <p className="text-gray-400 mb-6">
              Keep journaling to discover insights about your life
            </p>
            <Button 
              onClick={refreshPatterns} 
              disabled={refreshing}
              variant="ghost"
              size="sm"
              className="relative overflow-hidden group transition-all duration-200 bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 hover:text-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-secondary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              <span className="relative z-10 flex items-center font-medium">
                {refreshing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Analyze Entries
                  </>
                )}
              </span>
            </Button>
          </motion.div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col p-4 md:p-6 overflow-hidden">
      <div className="max-w-6xl mx-auto w-full flex flex-col flex-1">
        {/* Header */}
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white mb-1 flex items-center gap-2">
              <Diamond className="h-6 w-6 text-purple-500" />
              Pattern Insights
            </h2>
            <p className="text-gray-400 text-sm">
              Discover themes and patterns in your journal entries
            </p>
          </div>
          <Button 
            onClick={refreshPatterns} 
            disabled={refreshing}
            variant="ghost"
            size="sm"
            className="relative overflow-hidden group transition-all duration-200 bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 hover:text-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-secondary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            <span className="relative z-10 flex items-center font-medium">
              {refreshing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Refreshing...
                </>
              ) : (
                <>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Refresh
                </>
              )}
            </span>
          </Button>
        </div>

        <Tabs defaultValue="wordcloud" className="flex-1 flex flex-col overflow-hidden">
          <TabsList className="grid w-full max-w-md grid-cols-3 mb-4 bg-card/50 backdrop-blur-sm border border-border/50">
            <TabsTrigger value="wordcloud">Word Cloud</TabsTrigger>
            <TabsTrigger value="patterns">All Patterns</TabsTrigger>
            <TabsTrigger value="timeline">Timeline</TabsTrigger>
          </TabsList>

          <TabsContent value="wordcloud" className="flex-1 overflow-hidden">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-full">
              <Card className="lg:col-span-2 bg-card/50 backdrop-blur-sm border-border/50 flex flex-col">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Sparkles className="h-5 w-5" />
                    Your Journal Keywords
                  </CardTitle>
                  <CardDescription className="text-gray-400">
                    Click on words to see related patterns
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex-1 min-h-[400px]">
                  {wordCloudData.length > 0 && (
                    <WordCloud
                      words={wordCloudData}
                      onWordClick={handleWordClick}
                    />
                  )}
                </CardContent>
              </Card>

              <Card className="bg-card/50 backdrop-blur-sm border-border/50 overflow-hidden">
                <CardHeader>
                  <CardTitle className="text-white">Pattern Summary</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {Object.entries(patternsByType).map(([type, typePatterns]) => {
                    if (typePatterns.length === 0) return null
                    const Icon = getPatternIcon(type)
                    const colorClass = getPatternColor(type)
                    
                    return (
                      <div key={type} className="space-y-2">
                        <div className="flex items-center gap-2">
                          <Icon className={`h-4 w-4 ${colorClass}`} />
                          <span className="text-sm font-medium text-white capitalize">
                            {type} Patterns
                          </span>
                          <Badge variant="secondary" className="ml-auto">
                            {typePatterns.length}
                          </Badge>
                        </div>
                        <div className="space-y-1">
                          {typePatterns.slice(0, 3).map(pattern => (
                            <button
                              key={pattern.id}
                              onClick={() => setSelectedPattern(pattern)}
                              className="w-full text-left p-2 rounded-lg hover:bg-muted/50 transition-colors"
                            >
                              <p className="text-sm text-gray-300 truncate">
                                {pattern.description}
                              </p>
                              <p className="text-xs text-gray-500">
                                {pattern.frequency} occurrences
                              </p>
                            </button>
                          ))}
                        </div>
                      </div>
                    )
                  })}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="patterns" className="flex-1 overflow-y-auto">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {patterns.map(pattern => {
                const Icon = getPatternIcon(pattern.pattern_type)
                const colorClass = getPatternColor(pattern.pattern_type)
                
                return (
                  <motion.div
                    key={pattern.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    whileHover={{ scale: 1.02 }}
                  >
                    <Card 
                      className="bg-card/50 backdrop-blur-sm border-border/50 hover:bg-card/70 cursor-pointer transition-all"
                      onClick={() => setSelectedPattern(pattern)}
                    >
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <Icon className={`h-5 w-5 ${colorClass}`} />
                          <Badge variant="outline" className="text-xs">
                            {pattern.pattern_type}
                          </Badge>
                        </div>
                        <CardTitle className="text-white text-lg mt-2">
                          {pattern.description}
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-400">Frequency</span>
                            <span className="text-white font-medium">
                              {pattern.frequency} times
                            </span>
                          </div>
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-400">Confidence</span>
                            <span className="text-white font-medium">
                              {Math.round(pattern.confidence * 100)}%
                            </span>
                          </div>
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-400">First seen</span>
                            <span className="text-white">
                              {format(new Date(pattern.first_seen), 'MMM d')}
                            </span>
                          </div>
                        </div>
                        <div className="mt-3 flex flex-wrap gap-1">
                          {pattern.keywords.slice(0, 3).map((keyword, idx) => (
                            <Badge key={idx} variant="secondary" className="text-xs">
                              {keyword}
                            </Badge>
                          ))}
                          {pattern.keywords.length > 3 && (
                            <Badge variant="secondary" className="text-xs">
                              +{pattern.keywords.length - 3}
                            </Badge>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                )
              })}
            </div>
          </TabsContent>

          <TabsContent value="timeline" className="flex-1 overflow-y-auto">
            <Card className="bg-card/50 backdrop-blur-sm border-border/50">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Pattern Timeline
                </CardTitle>
                <CardDescription className="text-gray-400">
                  When patterns appear in your journal
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {patterns
                    .sort((a, b) => new Date(b.last_seen).getTime() - new Date(a.last_seen).getTime())
                    .map(pattern => {
                      const Icon = getPatternIcon(pattern.pattern_type)
                      const colorClass = getPatternColor(pattern.pattern_type)
                      
                      return (
                        <div 
                          key={pattern.id}
                          className="flex items-center gap-4 p-3 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
                          onClick={() => setSelectedPattern(pattern)}
                        >
                          <div className={`p-2 rounded-lg bg-muted/50`}>
                            <Icon className={`h-4 w-4 ${colorClass}`} />
                          </div>
                          <div className="flex-1">
                            <p className="text-white font-medium">
                              {pattern.description}
                            </p>
                            <p className="text-sm text-gray-400">
                              {format(new Date(pattern.first_seen), 'MMM d')} - {format(new Date(pattern.last_seen), 'MMM d, yyyy')}
                            </p>
                          </div>
                          <ChevronRight className="h-4 w-4 text-gray-400" />
                        </div>
                      )
                    })}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Pattern Details Modal */}
      <AnimatePresence>
        {selectedPattern && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
            onClick={() => setSelectedPattern(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-card border border-border rounded-lg p-6 max-w-lg w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  {(() => {
                    const Icon = getPatternIcon(selectedPattern.pattern_type)
                    const colorClass = getPatternColor(selectedPattern.pattern_type)
                    return <Icon className={`h-6 w-6 ${colorClass}`} />
                  })()}
                  <div>
                    <h3 className="text-xl font-bold text-white">
                      {selectedPattern.description}
                    </h3>
                    <p className="text-sm text-gray-400 capitalize">
                      {selectedPattern.pattern_type} Pattern
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedPattern(null)}
                >
                  ×
                </Button>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-400 mb-1">Frequency</p>
                    <p className="text-lg font-medium text-white">
                      {selectedPattern.frequency} occurrences
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400 mb-1">Confidence</p>
                    <p className="text-lg font-medium text-white">
                      {Math.round(selectedPattern.confidence * 100)}%
                    </p>
                  </div>
                </div>

                <div>
                  <p className="text-sm text-gray-400 mb-1">Time Range</p>
                  <p className="text-white">
                    {format(new Date(selectedPattern.first_seen), 'MMMM d, yyyy')} - {format(new Date(selectedPattern.last_seen), 'MMMM d, yyyy')}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-gray-400 mb-2">Keywords</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedPattern.keywords.map((keyword, idx) => (
                      <Badge key={idx} variant="secondary">
                        {keyword}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-sm text-gray-400 mb-2">Related Entries</p>
                  <p className="text-white">
                    This pattern appears in {selectedPattern.related_entries.length} journal entries
                  </p>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default PatternInsightsPage
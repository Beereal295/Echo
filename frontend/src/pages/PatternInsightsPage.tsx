import { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import WordCloud from '@/components/WordCloud'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Calendar as CalendarComponent } from '@/components/ui/calendar'
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
  Hash,
  Filter,
  X,
  ChevronDown,
  ChevronLeft,
  ExternalLink
} from 'lucide-react'
import { format } from 'date-fns'
import { useNavigate } from 'react-router-dom'

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
  const navigate = useNavigate()
  const [patterns, setPatterns] = useState<Pattern[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [selectedPattern, setSelectedPattern] = useState<Pattern | null>(null)
  const [showUnlockAnimation, setShowUnlockAnimation] = useState(false)
  
  // Keyword entries modal state
  const [selectedKeyword, setSelectedKeyword] = useState<string | null>(null)
  const [keywordEntries, setKeywordEntries] = useState<any[]>([])
  const [loadingKeywordEntries, setLoadingKeywordEntries] = useState(false)
  
  // Pattern entries modal state
  const [selectedPatternForEntries, setSelectedPatternForEntries] = useState<Pattern | null>(null)
  const [patternEntries, setPatternEntries] = useState<any[]>([])
  const [loadingPatternEntries, setLoadingPatternEntries] = useState(false)
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(12) // 12 patterns per page for grid layout
  
  // Date filtering state (exact same as ViewEntriesPage)
  const [showDateFilter, setShowDateFilter] = useState(false)
  const [dateFilterType, setDateFilterType] = useState<'all' | 'before' | 'after' | 'between' | 'on' | 'last-days-months'>('all')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [showBeforeCalendar, setShowBeforeCalendar] = useState(false)
  const [showAfterCalendar, setShowAfterCalendar] = useState(false)
  const [showOnCalendar, setShowOnCalendar] = useState(false)
  const [showBetweenStartCalendar, setShowBetweenStartCalendar] = useState(false)
  const [showBetweenEndCalendar, setShowBetweenEndCalendar] = useState(false)
  const [lastPeriodValue, setLastPeriodValue] = useState(1)
  const [lastPeriodUnit, setLastPeriodUnit] = useState<'days' | 'months'>('months')

  useEffect(() => {
    loadExistingPatterns()
  }, [])

  const loadExistingPatterns = async () => {
    setLoading(true)
    try {
      // Load existing patterns without checking threshold
      const patternsResponse = await api.getPatterns()
      if (patternsResponse.success && patternsResponse.data) {
        // Backend wraps data in SuccessResponse, so access nested data
        const patternsData = patternsResponse.data.data || patternsResponse.data
        setPatterns(patternsData.patterns || [])
        
        // Check if this is the first time viewing patterns
        const hasViewedPatterns = localStorage.getItem('hasViewedPatterns')
        if (!hasViewedPatterns && (patternsData.patterns || []).length > 0) {
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

  const generateInsights = async () => {
    setRefreshing(true)
    try {
      // Check if threshold is met before generating
      const thresholdResponse = await api.checkPatternThreshold()
      
      if (thresholdResponse.success && thresholdResponse.data) {
        // Backend wraps data in SuccessResponse, so access nested data
        const thresholdData = thresholdResponse.data.data || thresholdResponse.data
        
        if (!thresholdData.threshold_met) {
          // Show message about needing more entries
          toast({
            title: 'More entries needed',
            description: `You need ${thresholdData.remaining} more entries to unlock pattern insights.`,
            variant: 'default'
          })
          setRefreshing(false)
          return
        }
      }

      // Generate new patterns
      const response = await api.analyzePatterns()
      if (response.success) {
        // Backend wraps data in SuccessResponse, so access nested data
        const analyzeData = response.data?.data || response.data
        toast({
          title: 'Pattern analysis complete',
          description: `Found ${analyzeData.patterns_found || 0} new patterns`,
          variant: 'default'
        })
        
        // Reload patterns
        await loadExistingPatterns()
      }
    } catch (error) {
      console.error('Failed to generate patterns:', error)
      toast({
        title: 'Error generating patterns',
        description: 'Failed to analyze your journal entries for patterns',
        variant: 'destructive'
      })
    } finally {
      setRefreshing(false)
    }
  }

  const refreshPatterns = async () => {
    await generateInsights()
  }

  // Filter patterns based on date (exact same logic as ViewEntriesPage)
  const filteredPatterns = useMemo(() => {
    let filtered = patterns

    // Apply date filter
    if (dateFilterType !== 'all') {
      filtered = filtered.filter(pattern => {
        const patternDate = new Date(pattern.last_seen) // Use last_seen as primary date
        const today = new Date()
        
        switch (dateFilterType) {
          case 'before':
            return startDate ? patternDate < new Date(startDate) : true
          case 'after':
            return startDate ? patternDate > new Date(startDate) : true
          case 'on':
            if (startDate) {
              const selectedDate = new Date(startDate)
              const patternDateOnly = new Date(patternDate.getFullYear(), patternDate.getMonth(), patternDate.getDate())
              const selectedDateOnly = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate())
              return patternDateOnly.getTime() === selectedDateOnly.getTime()
            }
            return true
          case 'between':
            if (startDate && endDate) {
              return patternDate >= new Date(startDate) && patternDate <= new Date(endDate)
            }
            return true
          case 'last-days-months':
            const periodAgo = new Date()
            if (lastPeriodUnit === 'days') {
              periodAgo.setDate(today.getDate() - lastPeriodValue)
            } else {
              periodAgo.setMonth(today.getMonth() - lastPeriodValue)
            }
            return patternDate >= periodAgo
          default:
            return true
        }
      })
    }

    return filtered
  }, [patterns, dateFilterType, startDate, endDate, lastPeriodValue, lastPeriodUnit])

  // Generate word cloud data from all patterns
  const wordCloudData = useMemo(() => {
    const wordFrequency: Record<string, number> = {}
    
    filteredPatterns.forEach(pattern => {
      if (pattern.keywords) {
        pattern.keywords.forEach(keyword => {
          wordFrequency[keyword] = (wordFrequency[keyword] || 0) + pattern.frequency
        })
      }
    })

    return Object.entries(wordFrequency)
      .map(([text, value]) => ({ text, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 50) // Top 50 words
  }, [filteredPatterns])

  // Group patterns by type
  const patternsByType = useMemo(() => {
    const grouped: Record<string, Pattern[]> = {
      topic: [],
      mood: [],
      temporal: [],
      behavior: []
    }
    
    filteredPatterns.forEach(pattern => {
      if (grouped[pattern.pattern_type]) {
        grouped[pattern.pattern_type].push(pattern)
      }
    })
    
    return grouped
  }, [filteredPatterns])

  // Pagination logic
  const totalPages = Math.ceil(filteredPatterns.length / pageSize)
  const paginatedPatterns = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize
    return filteredPatterns.slice(startIndex, startIndex + pageSize)
  }, [filteredPatterns, currentPage, pageSize])

  // Reset pagination when filters change  
  useEffect(() => {
    setCurrentPage(1)
  }, [dateFilterType, startDate, endDate, lastPeriodValue, lastPeriodUnit])

  // Close date filter popup when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element
      if (showDateFilter && !target.closest('.date-filter-popup')) {
        setShowDateFilter(false)
        setShowBeforeCalendar(false)
        setShowAfterCalendar(false)
        setShowOnCalendar(false)
        setShowBetweenStartCalendar(false)
        setShowBetweenEndCalendar(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showDateFilter])

  // Pagination controls
  const goToPage = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page)
    }
  }

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

  const handleKeywordClick = async (keyword: string) => {
    setSelectedKeyword(keyword)
    setLoadingKeywordEntries(true)
    setKeywordEntries([])
    
    try {
      const response = await api.getEntriesByKeyword(keyword)
      
      if (response.success && response.data) {
        // Handle nested response structure similar to getPatterns
        const responseData = response.data.data || response.data
        const entries = responseData.entries || []
        
        setKeywordEntries(entries)
      } else {
        toast({
          title: 'Error loading entries',
          description: `Failed to load entries for keyword "${keyword}"`,
          variant: 'destructive'
        })
      }
    } catch (error) {
      console.error('Failed to load keyword entries:', error)
      toast({
        title: 'Error loading entries',
        description: `Failed to load entries for keyword "${keyword}"`,
        variant: 'destructive'
      })
    } finally {
      setLoadingKeywordEntries(false)
    }
  }

  const handlePatternEntriesClick = async (pattern: Pattern) => {
    setSelectedPatternForEntries(pattern)
    setLoadingPatternEntries(true)
    setPatternEntries([])
    
    try {
      const response = await api.getPatternEntries(pattern.id)
      
      if (response.success && response.data) {
        // Handle nested response structure
        const responseData = response.data.data || response.data
        const entries = responseData.entries || []
        
        setPatternEntries(entries)
      } else {
        toast({
          title: 'Error loading entries',
          description: `Failed to load entries for pattern "${pattern.description}"`,
          variant: 'destructive'
        })
      }
    } catch (error) {
      console.error('Failed to load pattern entries:', error)
      toast({
        title: 'Error loading entries',
        description: `Failed to load entries for pattern "${pattern.description}"`,
        variant: 'destructive'
      })
    } finally {
      setLoadingPatternEntries(false)
    }
  }

  const handleViewEntry = (entryId: number) => {
    // Navigate to View Entries page with the specific entry selected
    navigate('/entries', { state: { selectedEntryId: entryId } })
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
              onClick={generateInsights} 
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
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Refresh Insights
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
    <div className="h-screen flex flex-col p-4 md:p-6 relative">
      <div className="max-w-6xl mx-auto w-full flex flex-col flex-1">
        {/* Header */}
        <div className="mb-4 flex items-center justify-between flex-shrink-0">
          <div>
            <h2 className="text-2xl font-bold text-white mb-1 flex items-center gap-2">
              <Diamond className="h-6 w-6 text-purple-500" />
              Pattern Insights
            </h2>
            <p className="text-gray-400 text-sm">
              Discover themes and patterns in your journal entries
            </p>
          </div>
          <div className="flex items-center gap-2">
            {/* Date Filter Button */}
            <div className="relative">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowDateFilter(!showDateFilter)}
                className="flex items-center gap-2 relative overflow-hidden group transition-all duration-200 bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 hover:text-primary"
              >
                <div className="relative flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  {dateFilterType === 'all' ? 'All Time' : 
                   dateFilterType === 'last-days-months' ? `Last ${lastPeriodValue} ${lastPeriodUnit.charAt(0).toUpperCase() + lastPeriodUnit.slice(1)}` :
                   dateFilterType === 'before' ? 'Before Date' :
                   dateFilterType === 'after' ? 'After Date' :
                   dateFilterType === 'on' ? 'On Date' : 'Between Dates'}
                </div>
              </Button>

              {/* Date Filter Popup */}
              {showDateFilter && (
                <div className="date-filter-popup absolute top-full right-0 mt-2 w-96 bg-card border border-border rounded-lg shadow-xl z-50 p-4">
                  <div className="space-y-4">
                    <h3 className="font-semibold text-white text-sm">Filter by Date</h3>
                    
                    {/* Filter Type Selection */}
                    <div className="space-y-2">
                      <label className="flex items-center gap-2">
                        <input
                          type="radio"
                          name="dateFilter"
                          checked={dateFilterType === 'all'}
                          onChange={() => setDateFilterType('all')}
                          className="text-primary focus:ring-primary/20"
                        />
                        <span className="text-white text-sm">All time</span>
                      </label>
                      
                      <label className="flex items-center gap-2">
                        <input
                          type="radio"
                          name="dateFilter"
                          checked={dateFilterType === 'last-days-months'}
                          onChange={() => setDateFilterType('last-days-months')}
                          className="text-primary focus:ring-primary/20"
                        />
                        <span className="text-white text-sm">Last</span>
                        <input
                          type="number"
                          min="1"
                          max="31"
                          value={lastPeriodValue}
                          onChange={(e) => {
                            const value = Math.max(1, Math.min(31, parseInt(e.target.value) || 1))
                            setLastPeriodValue(value)
                          }}
                          disabled={dateFilterType !== 'last-days-months'}
                          className="bg-background border border-border rounded px-2 py-1 text-white text-sm w-16 focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20"
                        />
                        <div className="relative calendar-container">
                          <select
                            value={lastPeriodUnit}
                            onChange={(e) => setLastPeriodUnit(e.target.value as 'days' | 'months')}
                            disabled={dateFilterType !== 'last-days-months'}
                            className="bg-background border border-border rounded px-2 py-1 pr-6 text-white text-sm focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20 appearance-none"
                          >
                            <option value="days">Days</option>
                            <option value="months">Months</option>
                          </select>
                          <ChevronDown className="absolute right-1 top-1/2 transform -translate-y-1/2 h-3 w-3 text-muted-foreground pointer-events-none" />
                        </div>
                      </label>
                      
                      <label className="flex items-center gap-2">
                        <input
                          type="radio"
                          name="dateFilter"
                          checked={dateFilterType === 'before'}
                          onChange={() => setDateFilterType('before')}
                          className="text-primary focus:ring-primary/20"
                        />
                        <span className="text-white text-sm">Before</span>
                        <div className="relative calendar-container">
                          <button
                            type="button"
                            onClick={() => setShowBeforeCalendar(!showBeforeCalendar)}
                            disabled={dateFilterType !== 'before'}
                            className="bg-background border border-border rounded px-2 py-1 text-white text-sm w-32 text-left hover:bg-muted/50 disabled:opacity-50"
                          >
                            {startDate ? new Date(startDate).toLocaleDateString() : 'Select date'}
                          </button>
                          {showBeforeCalendar && dateFilterType === 'before' && (
                            <div className="absolute top-full left-0 mt-2 z-[100] min-w-[280px]">
                              <CalendarComponent
                                selected={startDate}
                                onSelect={(date) => {
                                  setStartDate(date)
                                  setShowBeforeCalendar(false)
                                }}
                                className="shadow-2xl border-2 border-border"
                              />
                            </div>
                          )}
                        </div>
                      </label>
                      
                      <label className="flex items-center gap-2">
                        <input
                          type="radio"
                          name="dateFilter"
                          checked={dateFilterType === 'after'}
                          onChange={() => setDateFilterType('after')}
                          className="text-primary focus:ring-primary/20"
                        />
                        <span className="text-white text-sm">After</span>
                        <div className="relative calendar-container">
                          <button
                            type="button"
                            onClick={() => setShowAfterCalendar(!showAfterCalendar)}
                            disabled={dateFilterType !== 'after'}
                            className="bg-background border border-border rounded px-2 py-1 text-white text-sm w-32 text-left hover:bg-muted/50 disabled:opacity-50"
                          >
                            {startDate ? new Date(startDate).toLocaleDateString() : 'Select date'}
                          </button>
                          {showAfterCalendar && dateFilterType === 'after' && (
                            <div className="absolute top-full left-0 mt-2 z-[100] min-w-[280px]">
                              <CalendarComponent
                                selected={startDate}
                                onSelect={(date) => {
                                  setStartDate(date)
                                  setShowAfterCalendar(false)
                                }}
                                className="shadow-2xl border-2 border-border"
                              />
                            </div>
                          )}
                        </div>
                      </label>
                      
                      <label className="flex items-center gap-2">
                        <input
                          type="radio"
                          name="dateFilter"
                          checked={dateFilterType === 'on'}
                          onChange={() => setDateFilterType('on')}
                          className="text-primary focus:ring-primary/20"
                        />
                        <span className="text-white text-sm">On</span>
                        <div className="relative calendar-container">
                          <button
                            type="button"
                            onClick={() => setShowOnCalendar(!showOnCalendar)}
                            disabled={dateFilterType !== 'on'}
                            className="bg-background border border-border rounded px-2 py-1 text-white text-sm w-32 text-left hover:bg-muted/50 disabled:opacity-50"
                          >
                            {startDate ? new Date(startDate).toLocaleDateString() : 'Select date'}
                          </button>
                          {showOnCalendar && dateFilterType === 'on' && (
                            <div className="absolute top-full left-0 mt-2 z-[100] min-w-[280px]">
                              <CalendarComponent
                                selected={startDate}
                                onSelect={(date) => {
                                  setStartDate(date)
                                  setShowOnCalendar(false)
                                }}
                                className="shadow-2xl border-2 border-border"
                              />
                            </div>
                          )}
                        </div>
                      </label>
                      
                      <label className="flex items-center gap-2">
                        <input
                          type="radio"
                          name="dateFilter"
                          checked={dateFilterType === 'between'}
                          onChange={() => setDateFilterType('between')}
                          className="text-primary focus:ring-primary/20"
                        />
                        <span className="text-white text-sm">Between</span>
                      </label>
                      
                      {dateFilterType === 'between' && (
                        <div className="ml-6 space-y-2">
                          <div className="flex items-center gap-2">
                            <span className="text-muted-foreground text-sm w-12">From:</span>
                            <div className="relative flex-1">
                              <button
                                type="button"
                                onClick={() => setShowBetweenStartCalendar(!showBetweenStartCalendar)}
                                className="bg-background border border-border rounded px-2 py-1 text-white text-sm w-full text-left hover:bg-muted/50"
                              >
                                {startDate ? new Date(startDate).toLocaleDateString() : 'Select date'}
                              </button>
                              {showBetweenStartCalendar && (
                                <div className="absolute top-full left-0 mt-2 z-[100] min-w-[280px]">
                                  <CalendarComponent
                                    selected={startDate}
                                    onSelect={(date) => {
                                      setStartDate(date)
                                      setShowBetweenStartCalendar(false)
                                    }}
                                    className="shadow-2xl border-2 border-border"
                                  />
                                </div>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-muted-foreground text-sm w-12">To:</span>
                            <div className="relative flex-1">
                              <button
                                type="button"
                                onClick={() => setShowBetweenEndCalendar(!showBetweenEndCalendar)}
                                className="bg-background border border-border rounded px-2 py-1 text-white text-sm w-full text-left hover:bg-muted/50"
                              >
                                {endDate ? new Date(endDate).toLocaleDateString() : 'Select date'}
                              </button>
                              {showBetweenEndCalendar && (
                                <div className="absolute top-full right-0 mt-2 z-[100] min-w-[280px]">
                                  <CalendarComponent
                                    selected={endDate}
                                    onSelect={(date) => {
                                      setEndDate(date)
                                      setShowBetweenEndCalendar(false)
                                    }}
                                    className="shadow-2xl border-2 border-border"
                                  />
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            <Button 
              onClick={generateInsights} 
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
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Refresh Insights
                  </>
                )}
              </span>
            </Button>
          </div>
        </div>

        <Tabs defaultValue="wordcloud" className="flex-1 flex flex-col">
          <TabsList className="grid w-full max-w-md grid-cols-3 mb-4 bg-card/50 backdrop-blur-sm border border-border/50 flex-shrink-0">
            <TabsTrigger value="wordcloud" className="flex items-center gap-2 data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
              Word Cloud
            </TabsTrigger>
            <TabsTrigger value="patterns" className="flex items-center gap-2 data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
              All Patterns
            </TabsTrigger>
            <TabsTrigger value="timeline" className="flex items-center gap-2 data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
              Timeline
            </TabsTrigger>
          </TabsList>

          <TabsContent value="wordcloud" className="flex-1">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="grid grid-cols-1 lg:grid-cols-4 gap-4" 
              style={{ minHeight: '600px' }}
            >
              <Card className="lg:col-span-3 bg-card/50 backdrop-blur-sm border-border/50 flex flex-col" style={{ minHeight: '600px' }}>
                <CardHeader className="flex-shrink-0">
                  <CardTitle className="text-white">
                    Your Journal Keywords
                  </CardTitle>
                  <CardDescription className="text-gray-400">
                    Click on words to see related patterns
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex-1" style={{ minHeight: '500px' }}>
                  {wordCloudData.length > 0 && (
                    <div className="w-full h-full" style={{ minHeight: '500px' }}>
                      <WordCloud
                        words={wordCloudData}
                        onWordClick={handleWordClick}
                        height={500}
                      />
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card className="bg-card/50 backdrop-blur-sm border-border/50 flex flex-col" style={{ minHeight: '600px' }}>
                <CardHeader className="pb-3 flex-shrink-0">
                  <CardTitle className="text-white text-lg">Pattern Summary</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 flex-1 overflow-y-auto">
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
                          <Badge className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20 text-xs ml-auto px-2 py-1 font-semibold">
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
                              <p className="text-xs text-gray-500 font-medium">
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
            </motion.div>
          </TabsContent>

          <TabsContent value="patterns" className="flex-1 flex flex-col overflow-hidden">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="flex-1 overflow-y-auto p-1"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-full">
                {paginatedPatterns.map(pattern => {
                const Icon = getPatternIcon(pattern.pattern_type)
                const colorClass = getPatternColor(pattern.pattern_type)
                
                return (
                  <motion.div
                    key={pattern.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    whileHover={{ scale: 1.02 }}
                    className="min-w-0 w-full"
                  >
                    <Card 
                      className="bg-card/50 backdrop-blur-sm border-border/50 hover:bg-card/70 cursor-pointer transition-all w-full min-w-0 h-full flex flex-col"
                      onClick={() => setSelectedPattern(pattern)}
                    >
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <Icon className={`h-5 w-5 ${colorClass}`} />
                          <Badge className="bg-purple-500/10 text-purple-400 border-purple-500/20 text-xs">
                            {pattern.pattern_type}
                          </Badge>
                        </div>
                        <CardTitle className="text-white text-lg mt-2">
                          {pattern.description}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="flex-1">
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
                            <Badge 
                              key={idx} 
                              className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20 text-xs cursor-pointer hover:bg-cyan-500/20 transition-colors"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleKeywordClick(keyword)
                              }}
                            >
                              {keyword}
                            </Badge>
                          ))}
                          {pattern.keywords.length > 3 && (
                            <Badge className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20 text-xs">
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
            
              {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="mt-4 flex items-center justify-between border-t border-border pt-4 flex-shrink-0">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => goToPage(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="flex items-center gap-2 bg-card border border-border text-yellow-400 hover:bg-card/80 hover:text-yellow-300 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </Button>
                
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>Page {currentPage} of {totalPages}</span>
                  <span className="text-xs">({filteredPatterns.length} total)</span>
                </div>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => goToPage(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="flex items-center gap-2 bg-card border border-border text-yellow-400 hover:bg-card/80 hover:text-yellow-300 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            )}
            </motion.div>
          </TabsContent>

          <TabsContent value="timeline" className="flex-1">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="flex flex-col"
            >
              <div className="flex-shrink-0 mb-3">
                <h3 className="text-white text-lg font-semibold flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Pattern Timeline
                </h3>
                <p className="text-gray-400 text-sm">
                  When patterns appear in your journal
                </p>
              </div>
              <div className="flex-1 overflow-y-auto">
                <div className="space-y-3">
                  {paginatedPatterns
                    .sort((a, b) => new Date(b.last_seen).getTime() - new Date(a.last_seen).getTime())
                    .map(pattern => {
                      const Icon = getPatternIcon(pattern.pattern_type)
                      const colorClass = getPatternColor(pattern.pattern_type)
                      
                      return (
                        <Card 
                          key={pattern.id}
                          className="bg-card/50 backdrop-blur-sm border-border/50 hover:bg-card/70 cursor-pointer transition-colors"
                          onClick={() => setSelectedPattern(pattern)}
                        >
                          <CardContent className="p-4">
                            <div className="flex items-center gap-4">
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
                                {pattern.keywords && pattern.keywords.length > 0 && (
                                  <div className="mt-2 flex flex-wrap gap-1">
                                    {pattern.keywords.slice(0, 3).map((keyword, idx) => (
                                      <Badge 
                                        key={idx} 
                                        className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20 text-xs cursor-pointer hover:bg-cyan-500/20 transition-colors"
                                        onClick={(e) => {
                                          e.stopPropagation()
                                          handleKeywordClick(keyword)
                                        }}
                                      >
                                        {keyword}
                                      </Badge>
                                    ))}
                                    {pattern.keywords.length > 3 && (
                                      <Badge className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20 text-xs">
                                        +{pattern.keywords.length - 3}
                                      </Badge>
                                    )}
                                  </div>
                                )}
                              </div>
                              <ChevronRight className="h-4 w-4 text-gray-400" />
                            </div>
                          </CardContent>
                        </Card>
                      )
                    })}
                </div>
              </div>
              
              {/* Timeline Pagination */}
              {totalPages > 1 && (
                <div className="mt-4 flex items-center justify-between border-t border-border pt-4 flex-shrink-0">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => goToPage(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="flex items-center gap-2 bg-card border border-border text-yellow-400 hover:bg-card/80 hover:text-yellow-300 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Previous
                  </Button>
                  
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span>Page {currentPage} of {totalPages}</span>
                    <span className="text-xs">({filteredPatterns.length} total)</span>
                  </div>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => goToPage(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="flex items-center gap-2 bg-card border border-border text-yellow-400 hover:bg-card/80 hover:text-yellow-300 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </motion.div>
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
                  className="h-8 w-8 p-0 text-blue-300 drop-shadow-[0_0_4px_rgba(147,197,253,0.6)] hover:bg-muted/50 hover:text-white hover:drop-shadow-[0_0_6px_rgba(255,255,255,0.6)]"
                  title="Close"
                >
                  <X className="h-4 w-4" />
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
                      <Badge 
                        key={idx} 
                        className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20 text-xs cursor-pointer hover:bg-cyan-500/20 transition-colors"
                        onClick={() => handleKeywordClick(keyword)}
                      >
                        {keyword}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-sm text-gray-400 mb-2">Related Entries</p>
                  <p className="text-white">
                    This pattern appears in{' '}
                    <button
                      onClick={() => handlePatternEntriesClick(selectedPattern)}
                      className="text-pink-400 hover:text-pink-300 underline cursor-pointer transition-colors font-medium"
                    >
                      {selectedPattern.related_entries.length} journal entries
                    </button>
                  </p>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Keyword Entries Modal */}
      <AnimatePresence>
        {selectedKeyword && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md"
            onClick={() => setSelectedKeyword(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="w-[95vw] h-[85vh] max-w-6xl bg-card border border-border rounded-lg shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="h-full flex flex-col">
                {/* Modal Header */}
                <div className="flex items-center justify-between p-6 border-b border-border">
                  <div>
                    <h2 className="text-xl font-bold text-white">
                      Entries containing "{selectedKeyword}"
                    </h2>
                    <p className="text-muted-foreground flex items-center gap-2 mt-1">
                      <Hash className="h-4 w-4" />
                      {keywordEntries.length} entries found
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedKeyword(null)}
                    className="h-8 w-8 p-0 text-blue-300 drop-shadow-[0_0_4px_rgba(147,197,253,0.6)] hover:bg-muted/50 hover:text-white hover:drop-shadow-[0_0_6px_rgba(255,255,255,0.6)]"
                    title="Close"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                {/* Modal Content */}
                <div className="flex-1 overflow-y-auto p-6">
                  {loadingKeywordEntries ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin text-primary" />
                      <span className="ml-2 text-gray-400">Loading entries...</span>
                    </div>
                  ) : keywordEntries.length === 0 ? (
                    <div className="text-center py-8">
                      <FileText className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                      <p className="text-white font-medium text-lg mb-2">No entries found</p>
                      <p className="text-muted-foreground">
                        No entries contain "{selectedKeyword}". This keyword might be generated from patterns or synonyms.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {keywordEntries.map((entry) => {
                        const formatTimestamp = (timestamp: string) => {
                          const date = new Date(timestamp)
                          const now = new Date()
                          const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))
                          
                          const dayOfWeek = date.toLocaleDateString('en-US', { weekday: 'long' })
                          const formattedDate = date.toLocaleDateString('en-US', { 
                            month: 'short', 
                            day: 'numeric',
                            year: diffInDays > 365 ? 'numeric' : undefined
                          })
                          const time = date.toLocaleTimeString('en-US', { 
                            hour: 'numeric', 
                            minute: '2-digit',
                            hour12: true 
                          })
                          
                          return { dayOfWeek, formattedDate, time }
                        }

                        const { dayOfWeek, formattedDate, time } = formatTimestamp(entry.timestamp)
                        
                        return (
                          <motion.div
                            key={entry.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="space-y-2"
                          >
                            <Card className="cursor-default hover:bg-muted/30 transition-all duration-200">
                              <CardHeader className="pb-3 pt-4 px-4">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <CardTitle className="text-sm font-medium">
                                      <span className="text-primary">{dayOfWeek}</span>
                                      <span className="text-white">, </span>
                                      <span className="text-muted-foreground">{formattedDate}</span>
                                    </CardTitle>
                                    <CardDescription className="flex items-center gap-2 mt-1 text-xs">
                                      <Clock className="h-3 w-3" />
                                      {time} • Entry #{entry.id}
                                    </CardDescription>
                                  </div>
                                  <button
                                    onClick={() => handleViewEntry(entry.id)}
                                    className="relative overflow-hidden group px-3 py-1.5 rounded-md font-medium shadow hover:shadow-lg hover:scale-[1.02] transition-all duration-300 cursor-pointer inline-flex items-center justify-center bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 text-sm"
                                  >
                                    <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-secondary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                                    <span className="relative z-10 flex items-center font-medium">
                                      <ExternalLink className="h-3 w-3 mr-1" />
                                      View
                                    </span>
                                  </button>
                                </div>
                              </CardHeader>
                              <CardContent className="px-4 pb-4">
                                <div className="text-white text-sm leading-relaxed whitespace-pre-wrap">
                                  {entry.structured_summary || entry.enhanced_text || entry.raw_text}
                                </div>
                                <div className="mt-4 pt-3 border-t border-border">
                                  <div className="flex items-center justify-between">
                                    {entry.mood_tags && entry.mood_tags.length > 0 && (
                                      <div className="flex flex-wrap gap-1">
                                        {entry.mood_tags.map((tag: string, tagIdx: number) => (
                                          <Badge key={tagIdx} className="bg-purple-500/10 text-purple-400 border-purple-500/20 text-xs">
                                            {tag}
                                          </Badge>
                                        ))}
                                      </div>
                                    )}
                                    <div className="text-xs text-muted-foreground ml-auto">
                                      {entry.word_count} words
                                    </div>
                                  </div>
                                </div>
                              </CardContent>
                            </Card>
                          </motion.div>
                        )
                      })}
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Pattern Entries Modal */}
      <AnimatePresence>
        {selectedPatternForEntries && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md"
            onClick={() => setSelectedPatternForEntries(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="w-[95vw] h-[85vh] max-w-6xl bg-card border border-border rounded-lg shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="h-full flex flex-col">
                {/* Modal Header */}
                <div className="flex items-center justify-between p-6 border-b border-border">
                  <div>
                    <h2 className="text-xl font-bold text-white">
                      Entries for "{selectedPatternForEntries.description}"
                    </h2>
                    <p className="text-muted-foreground flex items-center gap-2 mt-1">
                      <TrendingUp className="h-4 w-4" />
                      {patternEntries.length} entries found • {selectedPatternForEntries.pattern_type} pattern
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedPatternForEntries(null)}
                    className="h-8 w-8 p-0 text-blue-300 drop-shadow-[0_0_4px_rgba(147,197,253,0.6)] hover:bg-muted/50 hover:text-white hover:drop-shadow-[0_0_6px_rgba(255,255,255,0.6)]"
                    title="Close"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                {/* Modal Content */}
                <div className="flex-1 overflow-y-auto p-6">
                  {loadingPatternEntries ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin text-primary" />
                      <span className="ml-2 text-gray-400">Loading entries...</span>
                    </div>
                  ) : patternEntries.length === 0 ? (
                    <div className="text-center py-8">
                      <FileText className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                      <p className="text-white font-medium text-lg mb-2">No entries found</p>
                      <p className="text-muted-foreground">
                        No entries found for this pattern. The pattern data might be outdated.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {patternEntries.map((entry) => {
                        const formatTimestamp = (timestamp: string) => {
                          const date = new Date(timestamp)
                          const now = new Date()
                          const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))
                          
                          const dayOfWeek = date.toLocaleDateString('en-US', { weekday: 'long' })
                          const formattedDate = date.toLocaleDateString('en-US', { 
                            month: 'short', 
                            day: 'numeric',
                            year: diffInDays > 365 ? 'numeric' : undefined
                          })
                          const time = date.toLocaleTimeString('en-US', { 
                            hour: 'numeric', 
                            minute: '2-digit',
                            hour12: true 
                          })
                          
                          return { dayOfWeek, formattedDate, time }
                        }

                        const { dayOfWeek, formattedDate, time } = formatTimestamp(entry.timestamp)
                        
                        return (
                          <motion.div
                            key={entry.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="space-y-2"
                          >
                            <Card className="cursor-default hover:bg-muted/30 transition-all duration-200">
                              <CardHeader className="pb-3 pt-4 px-4">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <CardTitle className="text-sm font-medium">
                                      <span className="text-primary">{dayOfWeek}</span>
                                      <span className="text-white">, </span>
                                      <span className="text-muted-foreground">{formattedDate}</span>
                                    </CardTitle>
                                    <CardDescription className="flex items-center gap-2 mt-1 text-xs">
                                      <Clock className="h-3 w-3" />
                                      {time} • Entry #{entry.id}
                                    </CardDescription>
                                  </div>
                                  <button
                                    onClick={() => handleViewEntry(entry.id)}
                                    className="relative overflow-hidden group px-3 py-1.5 rounded-md font-medium shadow hover:shadow-lg hover:scale-[1.02] transition-all duration-300 cursor-pointer inline-flex items-center justify-center bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 text-sm"
                                  >
                                    <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-secondary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                                    <span className="relative z-10 flex items-center font-medium">
                                      <ExternalLink className="h-3 w-3 mr-1" />
                                      View
                                    </span>
                                  </button>
                                </div>
                              </CardHeader>
                              <CardContent className="px-4 pb-4">
                                <div className="text-white text-sm leading-relaxed whitespace-pre-wrap">
                                  {entry.structured_summary || entry.enhanced_text || entry.raw_text}
                                </div>
                                <div className="mt-4 pt-3 border-t border-border">
                                  <div className="flex items-center justify-between">
                                    {entry.mood_tags && entry.mood_tags.length > 0 && (
                                      <div className="flex flex-wrap gap-1">
                                        {entry.mood_tags.map((tag: string, tagIdx: number) => (
                                          <Badge key={tagIdx} className="bg-purple-500/10 text-purple-400 border-purple-500/20 text-xs">
                                            {tag}
                                          </Badge>
                                        ))}
                                      </div>
                                    )}
                                    <div className="text-xs text-muted-foreground ml-auto">
                                      {entry.word_count} words
                                    </div>
                                  </div>
                                </div>
                              </CardContent>
                            </Card>
                          </motion.div>
                        )
                      })}
                    </div>
                  )}
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
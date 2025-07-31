import { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  ChevronDown, 
  ChevronUp, 
  FileText, 
  Pen, 
  BookOpen, 
  Search,
  Filter,
  Calendar,
  Clock,
  Trash2,
  Download,
  ChevronLeft,
  ChevronRight,
  Loader2,
  MoreVertical,
  X,
  Maximize2,
  Edit,
  Save,
  CheckCircle
} from 'lucide-react'
import { api } from '@/lib/api'

// Types for entry data
interface Entry {
  id: number
  raw_text: string
  enhanced_text?: string
  structured_summary?: string
  mode: string
  timestamp: string
  word_count: number
  processing_metadata?: any
}

// View modes for entry display
const viewModes = [
  {
    key: 'raw',
    icon: FileText,
    title: "Raw Transcription",
    description: "Your exact words, unfiltered and authentic",
    gradient: "from-blue-500 to-blue-600",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/20"
  },
  {
    key: 'enhanced',
    icon: Pen,
    title: "Enhanced Style", 
    description: "Improved grammar and tone while preserving your intent",
    gradient: "from-purple-500 to-pink-500",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/20"
  },
  {
    key: 'structured',
    icon: BookOpen,
    title: "Structured Summary",
    description: "Organized into coherent themes and key points", 
    gradient: "from-emerald-500 to-teal-500",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/20"
  }
]

function ViewEntriesPage() {
  const [entries, setEntries] = useState<Entry[]>([])
  const [selectedEntry, setSelectedEntry] = useState<Entry | null>(null)
  const [expandedDropdowns, setExpandedDropdowns] = useState<Set<number>>(new Set())
  const [selectedVersion, setSelectedVersion] = useState<'raw' | 'enhanced' | 'structured'>('enhanced')
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [searching, setSearching] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalEntries, setTotalEntries] = useState(0)
  const [pageSize] = useState(20)
  const [deleting, setDeleting] = useState<number | null>(null)
  const [expandedView, setExpandedView] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editedContent, setEditedContent] = useState('')
  const [saving, setSaving] = useState(false)
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null)

  // Load entries on component mount and when page changes
  useEffect(() => {
    loadEntries()
  }, [currentPage])

  // Reload entries when not searching
  useEffect(() => {
    if (!searchQuery) {
      setCurrentPage(1)
      loadEntries()
    }
  }, [searchQuery])

  // Handle search with debouncing
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery !== '') {
        setSearching(true)
        setTimeout(() => setSearching(false), 500) // Simulate search time
      }
      setCurrentPage(1) // Reset to first page when searching
    }, 300)

    return () => clearTimeout(timer)
  }, [searchQuery])

  const loadEntries = async () => {
    try {
      setLoading(true)
      const response = await api.getEntries(currentPage, pageSize)
      
      if (response.success && response.data) {
        setEntries(response.data.entries || [])
        setTotalEntries(response.data.total || 0)
        setTotalPages(Math.ceil((response.data.total || 0) / pageSize))
      } else {
        console.error('Failed to load entries:', response.error)
        setEntries([])
      }
    } catch (error) {
      console.error('Failed to load entries:', error)
      setEntries([])
    } finally {
      setLoading(false)
    }
  }

  // Toggle dropdown for specific entry
  const toggleDropdown = (entryId: number) => {
    const newExpanded = new Set(expandedDropdowns)
    if (newExpanded.has(entryId)) {
      newExpanded.delete(entryId)
    } else {
      newExpanded.add(entryId)
    }
    setExpandedDropdowns(newExpanded)
  }

  // Delete entry
  const deleteEntry = async (entryId: number) => {
    try {
      setDeleting(entryId)
      const response = await api.deleteEntry(entryId)
      
      if (response.success) {
        setEntries(entries.filter(entry => entry.id !== entryId))
        if (selectedEntry?.id === entryId) {
          setSelectedEntry(null)
        }
        setTotalEntries(prev => prev - 1)
      } else {
        console.error('Failed to delete entry:', response.error)
      }
    } catch (error) {
      console.error('Failed to delete entry:', error)
    } finally {
      setDeleting(null)
    }
  }

  // Export entry
  const exportEntry = (entry: Entry, version: 'raw' | 'enhanced' | 'structured') => {
    const content = getEntryContent(entry, version)
    const { dayOfWeek, formattedDate } = formatTimestamp(entry.timestamp)
    const filename = `entry-${dayOfWeek}-${formattedDate}-${version}.txt`
    
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  // Export all versions of an entry
  const exportAllVersions = (entry: Entry) => {
    const { dayOfWeek, formattedDate } = formatTimestamp(entry.timestamp)
    const content = `
ENTRY - ${dayOfWeek}, ${formattedDate}
${'='.repeat(50)}

RAW TRANSCRIPTION:
${entry.raw_text}

${entry.enhanced_text ? `
ENHANCED STYLE:
${entry.enhanced_text}
` : ''}

${entry.structured_summary ? `
STRUCTURED SUMMARY:
${entry.structured_summary}
` : ''}

Created: ${formattedDate}
Word Count: ${entry.word_count}
    `.trim()
    
    const filename = `entry-${dayOfWeek}-${formattedDate}-all-versions.txt`
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  // Format timestamp for display
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const dayOfWeek = date.toLocaleDateString('en-US', { weekday: 'long' })
    const formattedDate = date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    })
    const time = date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    })
    
    return { dayOfWeek, formattedDate, time }
  }

  // Get content for specific version
  const getEntryContent = (entry: Entry, version: 'raw' | 'enhanced' | 'structured') => {
    switch (version) {
      case 'raw':
        return entry.raw_text
      case 'enhanced':
        return entry.enhanced_text || entry.raw_text
      case 'structured':
        return entry.structured_summary || entry.raw_text
      default:
        return entry.raw_text
    }
  }

  // Truncate text for preview
  const truncateText = (text: string, maxLength: number = 120) => {
    if (text.length <= maxLength) return text
    return text.slice(0, maxLength) + '...'
  }

  // Filter entries based on search query (client-side for now)
  const filteredEntries = useMemo(() => {
    if (!searchQuery) return entries
    
    return entries.filter(entry => 
      entry.raw_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
      entry.enhanced_text?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      entry.structured_summary?.toLowerCase().includes(searchQuery.toLowerCase())
    )
  }, [entries, searchQuery])

  // Edit functionality
  const startEditing = () => {
    if (selectedEntry) {
      setEditing(true)
      setEditedContent(getEntryContent(selectedEntry, selectedVersion))
    }
  }

  const cancelEditing = () => {
    setEditing(false)
    setEditedContent('')
  }

  const saveEntry = async () => {
    if (!selectedEntry || !editedContent.trim()) return

    try {
      setSaving(true)
      
      // Determine which field to update based on selected version
      const updateData: any = {}
      switch (selectedVersion) {
        case 'raw':
          updateData.raw_text = editedContent
          break
        case 'enhanced':
          updateData.enhanced_text = editedContent
          break
        case 'structured':
          updateData.structured_summary = editedContent
          break
      }

      const response = await api.updateEntry(selectedEntry.id, updateData)
      
      if (response.success && response.data) {
        // Update the entry in the local state
        const updatedEntries = entries.map(entry => 
          entry.id === selectedEntry.id ? response.data! : entry
        )
        setEntries(updatedEntries)
        setSelectedEntry(response.data)
        
        // Show success notification
        setNotification({ message: 'Entry updated successfully!', type: 'success' })
        
        // Reset editing state
        setEditing(false)
        setEditedContent('')
      } else {
        throw new Error(response.error || 'Failed to update entry')
      }
    } catch (error) {
      console.error('Failed to save entry:', error)
      setNotification({ 
        message: error instanceof Error ? error.message : 'Failed to update entry', 
        type: 'error' 
      })
    } finally {
      setSaving(false)
    }
  }

  // Auto-hide notification after 3 seconds
  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => {
        setNotification(null)
      }, 3000)
      return () => clearTimeout(timer)
    }
  }, [notification])

  // Pagination controls
  const goToPage = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page)
    }
  }

  return (
    <div className="h-screen flex flex-col p-4 md:p-6 relative">
      {/* Notification */}
      {notification && (
        <motion.div
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -50 }}
          className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-lg border shadow-lg ${
            notification.type === 'success' 
              ? 'bg-green-500/10 border-green-500/20 text-green-400' 
              : 'bg-red-500/10 border-red-500/20 text-red-400'
          }`}
        >
          {notification.type === 'success' ? (
            <CheckCircle className="h-4 w-4" />
          ) : (
            <X className="h-4 w-4" />
          )}
          <span className="text-sm font-medium">{notification.message}</span>
        </motion.div>
      )}
      
      <div className="max-w-7xl mx-auto w-full flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-6 flex-shrink-0">
          <h2 className="text-2xl font-bold text-white">Your Entries</h2>
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              {searching && (
                <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-primary animate-spin" />
              )}
              <input
                type="text"
                placeholder="Search entries..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-10 py-2 bg-background border border-border rounded-md text-white placeholder:text-muted-foreground focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200"
              />
            </div>
            <Badge className="bg-primary/10 text-primary border-primary/20">
              {searchQuery ? filteredEntries.length : totalEntries} entries
            </Badge>
          </div>
        </div>

        {/* Main Content - Split View */}
        <div className="flex-1 flex gap-6 overflow-hidden">
          {/* Entry List - Left Side */}
          <div className="w-96 flex flex-col overflow-hidden">
            <div className="flex-1 overflow-y-auto space-y-3 pr-2">
              {loading ? (
                <div className="flex items-center justify-center h-64">
                  <div className="text-center space-y-4">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                    <p className="text-muted-foreground">Loading entries...</p>
                  </div>
                </div>
              ) : filteredEntries.length === 0 ? (
                <div className="flex items-center justify-center h-64">
                  <div className="text-center space-y-4">
                    <FileText className="h-12 w-12 text-muted-foreground mx-auto" />
                    <p className="text-white font-medium">
                      {searchQuery ? 'No entries match your search' : 'Start by creating your first entry'}
                    </p>
                  </div>
                </div>
              ) : (
                filteredEntries.map((entry) => {
                  const { dayOfWeek, formattedDate, time } = formatTimestamp(entry.timestamp)
                  const isExpanded = expandedDropdowns.has(entry.id)
                  const isSelected = selectedEntry?.id === entry.id
                  
                  return (
                    <motion.div
                      key={entry.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="space-y-2"
                    >
                      {/* Entry Header - Always visible */}
                      <Card className={`cursor-pointer transition-all duration-200 hover:shadow-md ${
                        isSelected ? 'ring-2 ring-primary/50 bg-primary/5' : 'hover:bg-muted/30'
                      }`}>
                        <CardHeader 
                          className="pb-3 pt-4 px-4"
                          onClick={() => {
                            setSelectedEntry(entry)
                            setSelectedVersion('enhanced')
                          }}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className="flex flex-col">
                                <span className="font-semibold text-white text-sm">{dayOfWeek}</span>
                                <span className="text-muted-foreground text-xs">{formattedDate}</span>
                              </div>
                              <div className="flex items-center gap-1 text-muted-foreground">
                                <Clock className="h-3 w-3" />
                                <span className="text-xs">{time}</span>
                              </div>
                            </div>
                            <div className="flex items-center gap-1">
                              {/* Delete button */}
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  deleteEntry(entry.id)
                                }}
                                disabled={deleting === entry.id}
                                className="h-8 w-8 p-0 text-blue-300 drop-shadow-[0_0_4px_rgba(147,197,253,0.6)] hover:bg-red-500/20 hover:text-red-400 hover:drop-shadow-[0_0_6px_rgba(248,113,113,0.8)]"
                              >
                                {deleting === entry.id ? (
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                ) : (
                                  <Trash2 className="h-3 w-3" />
                                )}
                              </Button>
                              {/* Export button */}
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  exportAllVersions(entry)
                                }}
                                className="h-8 w-8 p-0 text-blue-300 drop-shadow-[0_0_4px_rgba(147,197,253,0.6)] hover:bg-blue-500/20 hover:text-blue-400 hover:drop-shadow-[0_0_6px_rgba(96,165,250,0.8)]"
                              >
                                <Download className="h-3 w-3" />
                              </Button>
                              {/* Dropdown toggle */}
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  toggleDropdown(entry.id)
                                }}
                                className="h-8 w-8 p-0 hover:bg-muted/50"
                              >
                                {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                              </Button>
                            </div>
                          </div>
                          
                          {/* Default Enhanced Preview */}
                          <div className="mt-2">
                            <p className="text-white text-sm leading-relaxed">
                              {truncateText(getEntryContent(entry, 'enhanced'))}
                            </p>
                            <div className="flex items-center justify-between mt-2">
                              <Badge className="bg-purple-500/10 text-purple-400 border-purple-500/20 text-xs">
                                Enhanced
                              </Badge>
                              <span className="text-muted-foreground text-xs">
                                {entry.word_count} words
                              </span>
                            </div>
                          </div>
                        </CardHeader>
                      </Card>

                      {/* Dropdown - All Three Versions */}
                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            transition={{ duration: 0.2 }}
                            className="space-y-2 ml-4"
                          >
                            {viewModes.map((mode) => {
                              const content = getEntryContent(entry, mode.key as any)
                              if (!content) return null
                              
                              return (
                                <Card
                                  key={mode.key}
                                  className={`cursor-pointer transition-all duration-200 hover:shadow-md ${mode.bgColor} ${mode.borderColor} border relative group`}
                                  onClick={() => {
                                    setSelectedEntry(entry)
                                    setSelectedVersion(mode.key as any)
                                  }}
                                >
                                  <CardContent className="p-3">
                                    <div className="flex items-center justify-between mb-2">
                                      <div className="flex items-center gap-2">
                                        <mode.icon className="h-4 w-4 text-white" />
                                        <span className="font-medium text-white text-sm">{mode.title}</span>
                                      </div>
                                      {/* Action buttons for dropdown entries */}
                                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100">
                                        <Button
                                          variant="ghost"
                                          size="sm"
                                          onClick={(e) => {
                                            e.stopPropagation()
                                            setSelectedEntry(entry)
                                            setSelectedVersion(mode.key as any)
                                            startEditing()
                                          }}
                                          className="h-6 w-6 p-0 text-blue-300 drop-shadow-[0_0_4px_rgba(147,197,253,0.6)] hover:bg-purple-500/20 hover:text-purple-400 hover:drop-shadow-[0_0_6px_rgba(196,181,253,0.8)]"
                                          title="Edit this version"
                                        >
                                          <Edit className="h-3 w-3" />
                                        </Button>
                                        <Button
                                          variant="ghost"
                                          size="sm"
                                          onClick={(e) => {
                                            e.stopPropagation()
                                            exportEntry(entry, mode.key as any)
                                          }}
                                          className="h-6 w-6 p-0 text-blue-300 drop-shadow-[0_0_4px_rgba(147,197,253,0.6)] hover:bg-blue-500/20 hover:text-blue-400 hover:drop-shadow-[0_0_6px_rgba(96,165,250,0.8)]"
                                          title="Export this version"
                                        >
                                          <Download className="h-3 w-3" />
                                        </Button>
                                        <Button
                                          variant="ghost"
                                          size="sm"
                                          onClick={(e) => {
                                            e.stopPropagation()
                                            deleteEntry(entry.id)
                                          }}
                                          disabled={deleting === entry.id}
                                          className="h-6 w-6 p-0 text-blue-300 drop-shadow-[0_0_4px_rgba(147,197,253,0.6)] hover:bg-red-500/20 hover:text-red-400 hover:drop-shadow-[0_0_6px_rgba(248,113,113,0.8)]"
                                          title="Delete entry"
                                        >
                                          {deleting === entry.id ? (
                                            <Loader2 className="h-3 w-3 animate-spin" />
                                          ) : (
                                            <Trash2 className="h-3 w-3" />
                                          )}
                                        </Button>
                                      </div>
                                    </div>
                                    <p className="text-white text-sm leading-relaxed">
                                      {truncateText(content, 100)}
                                    </p>
                                  </CardContent>
                                </Card>
                              )
                            })}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </motion.div>
                  )
                })
              )}
            </div>
            
            {/* Pagination Controls - Fixed at bottom */}
            {!searchQuery && totalPages > 1 && (
              <div className="mt-4 flex items-center justify-between border-t border-border pt-4 flex-shrink-0">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => goToPage(currentPage - 1)}
                  disabled={currentPage === 1 || loading}
                  className="flex items-center gap-2"
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </Button>
                
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>Page {currentPage} of {totalPages}</span>
                  <span className="text-xs">({totalEntries} total)</span>
                </div>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => goToPage(currentPage + 1)}
                  disabled={currentPage === totalPages || loading}
                  className="flex items-center gap-2"
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>

          {/* Entry Detail - Right Side */}
          <div className="flex-1 overflow-hidden">
            {selectedEntry ? (
              <Card className="h-full flex flex-col">
                <CardHeader className="border-b flex-shrink-0">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-white">
                        {formatTimestamp(selectedEntry.timestamp).dayOfWeek}, {formatTimestamp(selectedEntry.timestamp).formattedDate}
                      </CardTitle>
                      <CardDescription className="flex items-center gap-2 mt-1">
                        <Clock className="h-4 w-4" />
                        {formatTimestamp(selectedEntry.timestamp).time}
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-1">
                      {/* Action buttons for detail view - icon only */}
                      {editing ? (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={saveEntry}
                            disabled={saving || !editedContent.trim()}
                            className="h-8 w-8 p-0 text-blue-300 drop-shadow-[0_0_4px_rgba(147,197,253,0.6)] hover:bg-green-500/20 hover:text-green-400 hover:drop-shadow-[0_0_6px_rgba(74,222,128,0.8)]"
                            title="Save changes"
                          >
                            {saving ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Save className="h-4 w-4" />
                            )}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={cancelEditing}
                            className="h-8 w-8 p-0 text-blue-300 drop-shadow-[0_0_4px_rgba(147,197,253,0.6)] hover:bg-red-500/20 hover:text-red-400 hover:drop-shadow-[0_0_6px_rgba(248,113,113,0.8)]"
                            title="Cancel editing"
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </>
                      ) : (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={startEditing}
                            className="h-8 w-8 p-0 text-blue-300 drop-shadow-[0_0_4px_rgba(147,197,253,0.6)] hover:bg-purple-500/20 hover:text-purple-400 hover:drop-shadow-[0_0_6px_rgba(196,181,253,0.8)]"
                            title="Edit entry"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => exportEntry(selectedEntry, selectedVersion)}
                            className="h-8 w-8 p-0 text-blue-300 drop-shadow-[0_0_4px_rgba(147,197,253,0.6)] hover:bg-blue-500/20 hover:text-blue-400 hover:drop-shadow-[0_0_6px_rgba(96,165,250,0.8)]"
                            title={`Export ${viewModes.find(m => m.key === selectedVersion)?.title}`}
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setExpandedView(true)}
                        className="h-8 w-8 p-0 text-blue-300 drop-shadow-[0_0_4px_rgba(147,197,253,0.6)] hover:bg-green-500/20 hover:text-green-400 hover:drop-shadow-[0_0_6px_rgba(74,222,128,0.8)]"
                        title="Expand to full screen"
                      >
                        <Maximize2 className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deleteEntry(selectedEntry.id)}
                        disabled={deleting === selectedEntry.id}
                        className="h-8 w-8 p-0 text-blue-300 drop-shadow-[0_0_4px_rgba(147,197,253,0.6)] hover:bg-red-500/20 hover:text-red-400 hover:drop-shadow-[0_0_6px_rgba(248,113,113,0.8)]"
                        title="Delete entry"
                      >
                        {deleting === selectedEntry.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedEntry(null)}
                        className="h-8 w-8 p-0 text-blue-300 drop-shadow-[0_0_4px_rgba(147,197,253,0.6)] hover:bg-muted/50 hover:text-white hover:drop-shadow-[0_0_6px_rgba(255,255,255,0.6)]"
                        title="Close preview"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 mt-4">
                    {viewModes.map((mode) => (
                      <Button
                        key={mode.key}
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedVersion(mode.key as any)}
                        className={`relative overflow-hidden group transition-all duration-200 ${
                          selectedVersion === mode.key 
                            ? `${mode.bgColor} ${mode.borderColor} border text-white hover:${mode.bgColor} hover:text-white` 
                            : 'text-white border border-border hover:bg-muted/50 hover:text-white hover:border-muted'
                        }`}
                      >
                        {/* Animated background for active state */}
                        {selectedVersion === mode.key && (
                          <motion.div
                            layoutId="activeVersionBg"
                            className={`absolute inset-0 ${mode.gradient ? `bg-gradient-to-r ${mode.gradient}` : mode.bgColor}`}
                            initial={false}
                            transition={{ type: "spring", stiffness: 500, damping: 30 }}
                          />
                        )}
                        
                        <div className="relative flex items-center">
                          <mode.icon className="h-4 w-4 mr-2" />
                          {mode.title}
                        </div>
                      </Button>
                    ))}
                  </div>
                </CardHeader>
                <CardContent className="flex-1 overflow-y-auto p-6">
                  <div className="prose prose-invert max-w-none">
                    {editing ? (
                      <textarea
                        value={editedContent}
                        onChange={(e) => setEditedContent(e.target.value)}
                        className="w-full h-full min-h-[300px] bg-background border border-border rounded-md p-4 text-white text-sm leading-relaxed resize-none focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary/50"
                        placeholder="Edit your entry..."
                      />
                    ) : (
                      <p className="text-white leading-relaxed whitespace-pre-wrap text-sm">
                        {getEntryContent(selectedEntry, selectedVersion)}
                      </p>
                    )}
                  </div>
                  <div className="mt-6 pt-4 border-t border-border">
                    <div className="flex items-center justify-between text-sm text-muted-foreground">
                      <span>{selectedEntry.word_count} words</span>
                      <span>Created {formatTimestamp(selectedEntry.timestamp).formattedDate}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="h-full flex items-center justify-center">
                <div className="text-center space-y-4">
                  <FileText className="h-16 w-16 text-muted-foreground mx-auto" />
                  <div>
                    <p className="text-white font-medium text-lg">Select an entry to view</p>
                    <p className="text-muted-foreground">Choose an entry from the list to see its details</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Expanded View Modal */}
      <AnimatePresence>
        {expandedView && selectedEntry && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md"
            onClick={() => setExpandedView(false)}
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
                      {formatTimestamp(selectedEntry.timestamp).dayOfWeek}, {formatTimestamp(selectedEntry.timestamp).formattedDate}
                    </h2>
                    <p className="text-muted-foreground flex items-center gap-2 mt-1">
                      <Clock className="h-4 w-4" />
                      {formatTimestamp(selectedEntry.timestamp).time}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {/* Version selection in modal */}
                    {viewModes.map((mode) => (
                      <Button
                        key={mode.key}
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedVersion(mode.key as any)}
                        className={`relative overflow-hidden group transition-all duration-200 ${
                          selectedVersion === mode.key 
                            ? `${mode.bgColor} ${mode.borderColor} border text-white hover:${mode.bgColor} hover:text-white` 
                            : 'text-white border border-border hover:bg-muted/50 hover:text-white hover:border-muted'
                        }`}
                      >
                        {/* Animated background for active state */}
                        {selectedVersion === mode.key && (
                          <motion.div
                            layoutId="activeVersionBg"
                            className={`absolute inset-0 ${mode.gradient ? `bg-gradient-to-r ${mode.gradient}` : mode.bgColor}`}
                            initial={false}
                            transition={{ type: "spring", stiffness: 500, damping: 30 }}
                          />
                        )}
                        
                        <div className="relative flex items-center">
                          <mode.icon className="h-4 w-4 mr-2" />
                          {mode.title}
                        </div>
                      </Button>
                    ))}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setExpandedView(false)}
                      className="ml-4 h-8 w-8 p-0 text-blue-300 drop-shadow-[0_0_4px_rgba(147,197,253,0.6)] hover:bg-muted/50 hover:text-white hover:drop-shadow-[0_0_6px_rgba(255,255,255,0.6)]"
                      title="Close expanded view"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {/* Modal Content */}
                <div className="flex-1 overflow-y-auto p-6">
                  <div className="prose prose-invert max-w-none">
                    {editing ? (
                      <textarea
                        value={editedContent}
                        onChange={(e) => setEditedContent(e.target.value)}
                        className="w-full h-full min-h-[400px] bg-background border border-border rounded-md p-4 text-white text-sm leading-relaxed resize-none focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary/50"
                        placeholder="Edit your entry..."
                      />
                    ) : (
                      <p className="text-white leading-relaxed whitespace-pre-wrap text-sm">
                        {getEntryContent(selectedEntry, selectedVersion)}
                      </p>
                    )}
                  </div>
                </div>

                {/* Modal Footer */}
                <div className="border-t border-border p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      {editing ? (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={saveEntry}
                            disabled={saving || !editedContent.trim()}
                            className="flex items-center gap-2 hover:bg-green-500/20 hover:text-green-400 hover:border-green-500/50"
                          >
                            {saving ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Save className="h-4 w-4" />
                            )}
                            Save Changes
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={cancelEditing}
                            className="flex items-center gap-2 hover:bg-red-500/20 hover:text-red-400 hover:border-red-500/50"
                          >
                            <X className="h-4 w-4" />
                            Cancel
                          </Button>
                        </>
                      ) : (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={startEditing}
                            className="flex items-center gap-2 hover:bg-purple-500/20 hover:text-purple-400 hover:border-purple-500/50"
                          >
                            <Edit className="h-4 w-4" />
                            Edit Entry
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => exportEntry(selectedEntry, selectedVersion)}
                            className="flex items-center gap-2 hover:bg-blue-500/20 hover:text-blue-400 hover:border-blue-500/50"
                          >
                            <Download className="h-4 w-4" />
                            Export {viewModes.find(m => m.key === selectedVersion)?.title}
                          </Button>
                        </>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          deleteEntry(selectedEntry.id)
                          setExpandedView(false)
                        }}
                        disabled={deleting === selectedEntry.id}
                        className="flex items-center gap-2 hover:bg-red-500/20 hover:text-red-400 hover:border-red-500/50"
                      >
                        {deleting === selectedEntry.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                        Delete Entry
                      </Button>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      <span>{selectedEntry.word_count} words</span>
                      <span className="mx-2">•</span>
                      <span>Created {formatTimestamp(selectedEntry.timestamp).formattedDate}</span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default ViewEntriesPage
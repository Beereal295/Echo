// API client for Echo Journal backend

const API_BASE_URL = 'http://localhost:8000/api/v1'

interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
}

interface Entry {
  id: number
  raw_text: string
  enhanced_text?: string
  structured_summary?: string
  mode: string
  embeddings?: string
  timestamp: string
  mood_tags?: string[]
  word_count: number
  processing_metadata?: any
}

interface EntryCreate {
  raw_text: string
  mode: string
}

interface EntryListResponse {
  entries: Entry[]
  total: number
  page: number
  page_size: number
  has_next: boolean
  has_prev: boolean
}

interface Preference {
  id: number
  key: string
  value: string
  value_type: string
  description?: string
  typed_value: any
}

interface PreferencesListResponse {
  preferences: Preference[]
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
    }

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        return {
          success: false,
          error: errorData.detail || `HTTP ${response.status}: ${response.statusText}`
        }
      }

      const data = await response.json()
      return {
        success: true,
        data
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error'
      }
    }
  }

  // Entry endpoints
  async createEntry(entryData: EntryCreate): Promise<ApiResponse<Entry>> {
    return this.request<Entry>('/entries/', {
      method: 'POST',
      body: JSON.stringify(entryData)
    })
  }

  async createEntryWithAllTexts(
    rawText: string,
    enhancedText?: string,
    structuredSummary?: string,
    mode: string = 'raw'
  ): Promise<ApiResponse<Entry>> {
    return this.request<Entry>('/entries/', {
      method: 'POST',
      body: JSON.stringify({
        raw_text: rawText,
        enhanced_text: enhancedText,
        structured_summary: structuredSummary,
        mode
      })
    })
  }

  async getEntries(
    page: number = 1,
    pageSize: number = 20,
    mode?: string
  ): Promise<ApiResponse<EntryListResponse>> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString()
    })
    
    if (mode) {
      params.append('mode', mode)
    }

    return this.request<EntryListResponse>(`/entries/?${params}`)
  }

  async getEntry(entryId: number): Promise<ApiResponse<Entry>> {
    return this.request<Entry>(`/entries/${entryId}`)
  }

  async updateEntry(entryId: number, entryData: Partial<EntryCreate>): Promise<ApiResponse<Entry>> {
    return this.request<Entry>(`/entries/${entryId}`, {
      method: 'PUT',
      body: JSON.stringify(entryData)
    })
  }

  async deleteEntry(entryId: number): Promise<ApiResponse<any>> {
    return this.request(`/entries/${entryId}`, {
      method: 'DELETE'
    })
  }

  // Entry processing endpoints
  async processEntry(entryId: number, mode: string): Promise<ApiResponse<any>> {
    return this.request(`/entries/process/${entryId}`, {
      method: 'POST',
      body: JSON.stringify({ mode })
    })
  }

  async processTextOnly(
    rawText: string,
    modes: string[]
  ): Promise<ApiResponse<any>> {
    return this.request('/entries/process-only', {
      method: 'POST',
      body: JSON.stringify({
        raw_text: rawText,
        modes
      })
    })
  }

  async createAndProcessEntry(
    rawText: string,
    modes: string[]
  ): Promise<ApiResponse<any>> {
    return this.request('/entries/create-and-process', {
      method: 'POST',
      body: JSON.stringify({
        raw_text: rawText,
        modes
      })
    })
  }

  async getJobStatus(jobId: string): Promise<ApiResponse<any>> {
    return this.request(`/entries/processing/job/${jobId}`)
  }

  async getQueueStatus(): Promise<ApiResponse<any>> {
    return this.request('/entries/processing/queue/status')
  }

  // Health and status endpoints
  async getHealth(): Promise<ApiResponse<any>> {
    return this.request('/health')
  }

  async getWebSocketStatus(): Promise<ApiResponse<any>> {
    return this.request('/ws/status')
  }

  // Ollama endpoints
  async getOllamaModels(): Promise<ApiResponse<string[]>> {
    return this.request('/ollama/models')
  }

  async testOllamaConnection(): Promise<ApiResponse<any>> {
    return this.request('/ollama/test', {
      method: 'POST'
    })
  }

  // STT endpoints
  async getSTTStatus(): Promise<ApiResponse<any>> {
    return this.request('/stt/status')
  }

  async updateSTTConfig(config: any): Promise<ApiResponse<any>> {
    return this.request('/stt/config', {
      method: 'POST',
      body: JSON.stringify(config)
    })
  }

  // Hotkey endpoints
  async getHotkeyStatus(): Promise<ApiResponse<any>> {
    return this.request('/hotkey/status')
  }

  async changeHotkey(newHotkey: string): Promise<ApiResponse<any>> {
    return this.request('/hotkey/change', {
      method: 'POST',
      body: JSON.stringify({ hotkey: newHotkey })
    })
  }

  async validateHotkey(hotkey: string): Promise<ApiResponse<any>> {
    return this.request('/hotkey/validate', {
      method: 'POST',
      body: JSON.stringify({ hotkey })
    })
  }

  // Preferences endpoints
  async getPreferences(): Promise<ApiResponse<PreferencesListResponse>> {
    return this.request<PreferencesListResponse>('/preferences/')
  }

  async updatePreference(key: string, value: any): Promise<ApiResponse<any>> {
    return this.request('/preferences/', {
      method: 'POST',
      body: JSON.stringify({ key, value })
    })
  }

  // Statistics
  async getEntryCount(): Promise<ApiResponse<{ total_entries: number }>> {
    return this.request('/entries/stats/count')
  }

  // Semantic search
  async semanticSearch(query: string, limit: number = 10, similarityThreshold: number = 0.3): Promise<ApiResponse<any>> {
    return this.request('/embeddings/semantic-search', {
      method: 'POST',
      body: JSON.stringify({
        query,
        limit,
        similarity_threshold: similarityThreshold
      })
    })
  }


  // Regenerate all embeddings using raw text only
  async regenerateAllEmbeddings(): Promise<ApiResponse<any>> {
    return this.request('/embeddings/regenerate-all-raw-text', {
      method: 'POST'
    })
  }

  // Get regeneration status
  async getRegenerationStatus(): Promise<ApiResponse<any>> {
    return this.request('/embeddings/regeneration-status')
  }

  // Debug database state
  async debugDatabaseState(): Promise<ApiResponse<any>> {
    return this.request('/embeddings/debug-database')
  }

  // Test embeddings directly
  async testEmbeddings(): Promise<ApiResponse<any>> {
    return this.request('/embeddings/test-embeddings')
  }

  // Force clear all embeddings
  async forceClearEmbeddings(): Promise<ApiResponse<any>> {
    return this.request('/embeddings/force-clear-embeddings', {
      method: 'POST'
    })
  }

  // Synchronous regeneration (for testing)
  async regenerateSync(): Promise<ApiResponse<any>> {
    return this.request('/embeddings/regenerate-sync', {
      method: 'POST'
    })
  }

  // Debug search
  async debugSearch(query: string): Promise<ApiResponse<any>> {
    return this.request('/embeddings/debug-search', {
      method: 'POST',
      body: JSON.stringify({ query })
    })
  }

  // Fix hiking entries
  async fixHikingEntries(): Promise<ApiResponse<any>> {
    return this.request('/embeddings/fix-hiking-entries', {
      method: 'POST'
    })
  }

  // Regenerate all embeddings with raw text only (final fix)
  async regenerateAllRawText(): Promise<ApiResponse<any>> {
    return this.request('/embeddings/regenerate-all-raw-text', {
      method: 'POST'
    })
  }

  // Pattern API methods
  async checkPatternThreshold(): Promise<ApiResponse<{
    threshold_met: boolean
    threshold: number
    entry_count: number
    remaining: number
  }>> {
    return this.request('/patterns/check')
  }

  async analyzePatterns(): Promise<ApiResponse<{
    patterns_found: number
    pattern_types: Record<string, number>
  }>> {
    return this.request('/patterns/analyze', {
      method: 'POST'
    })
  }

  async getPatterns(): Promise<ApiResponse<{
    patterns: Array<{
      id: number
      pattern_type: string
      description: string
      frequency: number
      confidence: number
      first_seen: string
      last_seen: string
      related_entries: number[]
      keywords: string[]
    }>
    total: number
  }>> {
    return this.request('/patterns/')
  }

  async getPatternEntries(patternId: number): Promise<ApiResponse<{
    entries: Entry[]
    pattern_id: number
    total: number
  }>> {
    return this.request(`/patterns/entries/${patternId}`)
  }
  
  async getEntriesByKeyword(keyword: string): Promise<ApiResponse<{
    entries: Entry[]
    keyword: string
    total: number
  }>> {
    return this.request(`/patterns/keyword/${encodeURIComponent(keyword)}`)
  }

  // Mood analysis endpoints
  async analyzeMood(text: string): Promise<ApiResponse<{
    mood_tags: string[]
  }>> {
    return this.request('/entries/analyze-mood', {
      method: 'POST',
      body: JSON.stringify({ text })
    })
  }

  async analyzeEntryMood(entryId: number): Promise<ApiResponse<{
    entry_id: number
    status: string
  }>> {
    return this.request(`/entries/${entryId}/analyze-mood`, {
      method: 'POST'
    })
  }
}

// Export singleton instance
export const api = new ApiClient()
export type { Entry, EntryCreate, EntryListResponse, ApiResponse, Preference, PreferencesListResponse }
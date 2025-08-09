# Memory Pagination API Implementation Plan

## Current Problem

The MemoriesPage currently loads only 20 unrated memories using `getUnratedMemories(20)`, which creates several issues:

- **Limited Collection View**: Memory collection only shows 20 memories instead of all 1250+ available
- **Incorrect Pagination**: Shows "Page 1 of 3" instead of actual "Page 1 of 208+"
- **Mixed Concerns**: Single API serves both swipe functionality and collection browsing
- **No Filter Support**: Cannot filter between rated/unrated/all memories for future features

## Proposed Solution: Backend Pagination API

### 1. New Backend API Endpoint

Create a new paginated memories endpoint:

```
GET /api/memories?page=1&limit=6&filter=all
```

**Query Parameters:**
- `page`: Page number (1-based indexing)
- `limit`: Number of memories per page (default: 6)
- `filter`: Memory filter type
  - `all` - All memories (rated + unrated)
  - `rated` - Only rated memories (user_rated = 1)
  - `unrated` - Only unrated memories (user_rated = 0)

**Response Format:**
```typescript
{
  memories: Memory[],           // Array of 6 memories for current page
  total: 1250,                  // Total available memories (filtered)
  page: 1,                      // Current page number
  totalPages: 208,              // Total pages calculated
  hasNext: true,                // Has next page
  hasPrev: false,               // Has previous page
  filter: "all"                 // Applied filter
}
```

### 2. Frontend API Client Changes

Add new method to `api.ts`:

```typescript
async getPaginatedMemories(
  page: number = 1, 
  limit: number = 6, 
  filter: 'all' | 'rated' | 'unrated' = 'all'
): Promise<ApiResponse<{
  memories: Memory[]
  total: number
  page: number
  totalPages: number
  hasNext: boolean
  hasPrev: boolean
  filter: string
}>> {
  const params = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
    filter
  })
  return this.request(`/memories?${params}`)
}
```

### 3. Frontend State Management

**Separate Data Sources:**
```typescript
// For swipe functionality (left card)
const [unratedMemories, setUnratedMemories] = useState<Memory[]>([])

// For collection browsing (right card)  
const [allMemories, setAllMemories] = useState<Memory[]>([])
const [memoryPage, setMemoryPage] = useState(1)
const [memoryTotalPages, setMemoryTotalPages] = useState(1)
const [memoryFilter, setMemoryFilter] = useState<'all' | 'rated' | 'unrated'>('all')

// Currently selected memory (can be from either source)
const [currentMemory, setCurrentMemory] = useState<Memory | null>(null)
const [currentMemorySource, setCurrentMemorySource] = useState<'swipe' | 'collection'>('swipe')
```

### 4. Memory Selection Logic

**Dynamic Left Card Display:**
```typescript
const getDisplayMemory = () => {
  if (currentMemorySource === 'collection' && currentMemory) {
    return currentMemory
  }
  return unratedMemories[currentIndex] // Default swipe behavior
}

const canRate = () => {
  const memory = getDisplayMemory()
  return memory && memory.user_rated === 0
}

const getPreviousRating = () => {
  const memory = getDisplayMemory()
  if (memory && memory.user_rated === 1) {
    return memory.user_score_adjustment > 0 ? 'relevant' : 'irrelevant'
  }
  return null
}
```

### 5. Updated Load Functions

**Separate Loading:**
```typescript
const loadUnratedMemories = async () => {
  // For swipe functionality only
  const response = await api.getUnratedMemories(20)
  if (response.success) {
    setUnratedMemories(response.data)
  }
}

const loadPaginatedMemories = async (page: number = 1, filter: string = 'all') => {
  // For collection browsing
  const response = await api.getPaginatedMemories(page, 6, filter)
  if (response.success) {
    setAllMemories(response.data.memories)
    setMemoryTotalPages(response.data.totalPages)
    // Update pagination display with real numbers
  }
}
```

### 6. UI Updates

**Left Card States:**
- **Swipe Mode**: Shows rating buttons for unrated memories
- **Collection Mode**: 
  - If selected memory is unrated → Show rating buttons
  - If selected memory is rated → Show previous rating badge (relevant/irrelevant)

**Right Card Features:**
- **Pagination**: "Page 5 of 208 (1,250 total)" - real numbers
- **Filter Dropdown** (future): All/Rated/Unrated memories
- **Click Selection**: Click any memory to view/rate on left card

### 7. Rating Action Updates

**When User Rates Memory:**
```typescript
const handleRateMemory = async (memoryId: number, isRelevant: boolean) => {
  await api.rateMemory(memoryId, isRelevant ? 2 : -3)
  
  if (currentMemorySource === 'swipe') {
    // Remove from unrated queue, move to next
    moveToNextUnratedMemory()
  } else {
    // Update memory in collection, show new rating status
    updateMemoryInCollection(memoryId, isRelevant)
  }
  
  // Refresh stats
  loadStats()
}
```

### 8. Performance Benefits

- **Efficient Loading**: Only loads 6 memories per request instead of 1250+
- **Backend Filtering**: Database handles filtering before pagination
- **Cached Results**: Frontend can cache pages for quick navigation
- **Scalable**: Handles any number of memories without performance impact

### 9. Future Enhancements

**Filter Implementation:**
```typescript
const handleFilterChange = (newFilter: 'all' | 'rated' | 'unrated') => {
  setMemoryFilter(newFilter)
  setMemoryPage(1) // Reset to first page
  loadPaginatedMemories(1, newFilter)
}
```

**Search Integration:**
- Add search parameter to pagination API
- Combine search + filter + pagination in single endpoint

## Implementation Steps

1. **Backend**: Create paginated memories endpoint with filtering
2. **API Client**: Add `getPaginatedMemories` method
3. **Frontend**: Separate swipe and collection state management
4. **UI**: Update pagination display with real numbers
5. **Selection Logic**: Handle memory selection from collection
6. **Rating Updates**: Update both swipe queue and collection
7. **Testing**: Verify with 1250+ memories
8. **Filter UI**: Add dropdown for memory type filtering (future)

## Expected Results

- **Collection Access**: Users can browse all 1250+ memories
- **Real Pagination**: "Page 15 of 208 (1,250 total)" instead of fake numbers
- **Efficient Performance**: Only loads 6 memories at a time
- **Proper Selection**: Click any memory to rate/view on left card
- **Filter Ready**: Backend prepared for rated/unrated filtering
- **Scalable**: Handles any number of memories efficiently

---

**Status**: Ready for implementation
**Priority**: High - Blocks user access to complete memory history
**Estimated Time**: 2-3 hours (backend + frontend integration)
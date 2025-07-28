# Project Overview: Personal Journal with AI

## Core Idea
A lightweight, local-first journaling tool that transcribes user speech and organizes entries into readable, coherent thoughts. The user can choose how the journal writes—raw transcription, improved tone, or high-level structured summaries. The app communicates with Ollama via REST API to keep the application lightweight.

## Features

### Modes of Entry
- **Raw Transcription**: Direct speech-to-text output.
- **Enhanced Style**: Improves grammar and tone while preserving intent.
- **Structured Summary**: Consolidates ideas into well-organized paragraphs with logical flow.

Each mode becomes a "card" that users can select before or after input. These entries are stored locally.

### Talk to Your Diary
A conversational feature that acts like a pseudo-therapist without claiming medical support. It allows users to:
- Ask questions like "What did I do last Tuesday?"
- Reflect on recurring emotions or behavior patterns.
- Get feedback based on previous structured entries.

### Pattern Detection (Available After 30 Entries)
- Once a user has made 30 or more entries, the app unlocks a feature to assess recurring themes and behaviors.
- Automatically identifies patterns in mood, activities, or frequently mentioned topics.
- Summarizes and lists observed habits or changes over time.

### Local-first + Offline Capabilities
- All data stays on the user's machine.
- Option to connect with their Ollama server for LLM-based inference.
- SQLite used for lightweight and portable database storage.

## Tech Stack

### Backend
- Python (FastAPI or similar HTTP framework)
- Integration with local LLMs (Whisper, Ollama, etc.)

### Frontend
- PWA (Progressive Web App)
- Svelte for sleek UI that feels relaxing and intentional
- Packaged with PyInstaller for cross-platform distribution (Windows `.exe`, Mac `.app`)

### Database
- SQLite: simple, local, and easy to integrate
- Text embeddings generated via a local model like `BGE-small`
- Embeddings stored directly in SQLite as JSON or blob fields
- Custom logic for vector similarity search (e.g., cosine similarity) handled manually within the app logic

### Key Library Versions (as of July 2025)
- **FastAPI**: 0.115.12 (latest stable)
- **sentence-transformers**: Latest version with full BGE model support
- **SQLite**: Built into Python, no version concerns
- **Pydantic**: v2.x (comes with FastAPI)
- **httpx**: For async HTTP calls to Ollama API (no heavy SDK needed)

## Backend Architecture Deep Dive

### Core Database Schema

#### Entries Table
```sql
entries (
    id INTEGER PRIMARY KEY,
    raw_text TEXT NOT NULL,
    enhanced_text TEXT,
    structured_summary TEXT,
    mode TEXT NOT NULL,
    embeddings TEXT,  -- JSON array of floats
    timestamp DATETIME,
    mood_tags TEXT,   -- JSON array of strings
    word_count INTEGER,
    processing_metadata TEXT  -- JSON with model used, processing time, etc.
)
```

#### Patterns Table
```sql
patterns (
    id INTEGER PRIMARY KEY,
    pattern_type TEXT,  -- 'mood', 'topic', 'behavior', 'temporal'
    description TEXT,
    frequency INTEGER,
    confidence REAL,    -- 0.0 to 1.0
    first_seen DATE,
    last_seen DATE,
    related_entries TEXT  -- JSON array of entry IDs
)
```

### Memory System Architecture

#### Embedding Strategy
- **Model**: BGE-small (BAAI/bge-small-en-v1.5) - 384 dimensions
- **What to embed**: For each entry, create embeddings for:
  - Full raw text (primary embedding)
  - Structured summary if available (secondary embedding)
  - Individual sentences for fine-grained retrieval

#### Storage Approach
```python
# Embeddings stored as JSON in SQLite
embedding_data = {
    "full_text": [0.1, 0.2, ...],  # 384 dims
    "summary": [0.1, 0.2, ...],     # 384 dims if exists
    "sentences": [                   # For detailed retrieval
        {"text": "I felt great today.", "embedding": [...]},
        {"text": "Work was challenging.", "embedding": [...]}
    ]
}
```

#### Retrieval Pipeline
1. **Query Processing**
   - User asks: "When was I happy last week?"
   - Generate query embedding
   - Extract temporal constraints ("last week")

2. **Multi-Stage Retrieval**
   ```python
   # Stage 1: Temporal filtering (if applicable)
   # Stage 2: Semantic search on full_text embeddings
   # Stage 3: Re-rank using summary embeddings
   # Stage 4: Fine-tune with sentence-level matching
   ```

3. **Similarity Calculation**
   - Use cosine similarity for semantic matching
   - Combine with temporal proximity scoring
   - Weight recent entries slightly higher for relevance

#### Caching Strategy
- Cache top-K similar entries for common query patterns
- Implement simple LRU cache for embedding computations
- Pre-compute daily/weekly summaries for faster pattern detection

### Milestone & Notification System

#### Milestone Types
1. **Pattern Unlock Celebration** (30 entries)
   - One-time popup when user reaches 30 entries
   - "🎉 Pattern Insights Unlocked! Your diary can now identify recurring themes in your thoughts."
   - Animated confetti effect

2. **Buy Me a Coffee** (7 days of usage)
   - Shows after 7 days of active use
   - "☕ Enjoying your journal? If this app has helped you, consider buying me a coffee!"
   - Shows every 30 days if dismissed
   - Includes "Support" and "Maybe Later" buttons

3. **Entry Creation Success**
   - Brief toast notification after creating entries
   - Shows checkmarks for each mode created

#### Implementation
```python
# Milestone checking logic
async def check_milestones(user_id: int):
    milestones = []
    
    # Check 30 entries milestone
    entry_count = get_entry_count(user_id)
    if entry_count == 30 and not get_preference("pattern_unlock_shown"):
        milestones.append({
            "type": "pattern_unlock",
            "title": "Pattern Insights Unlocked!",
            "message": "Your diary can now identify recurring themes",
            "icon": "🎉"
        })
    
    # Check 7-day usage milestone
    first_use = get_preference("first_use_date")
    if first_use:
        days_used = (datetime.now() - first_use).days
        coffee_shown = get_preference("coffee_popup_shown")
        coffee_dismissed = get_preference("coffee_popup_dismissed_date")
        
        # Show after 7 days, then every 30 days if dismissed
        if days_used >= 7 and not coffee_shown:
            milestones.append({
                "type": "coffee",
                "title": "Enjoying Your Journal?",
                "message": "If this app has helped you, consider buying me a coffee!",
                "icon": "☕",
                "actions": ["support", "later"]
            })
        elif coffee_dismissed:
            days_since_dismissed = (datetime.now() - coffee_dismissed).days
            if days_since_dismissed >= 30:
                milestones.append({
                    "type": "coffee",
                    "title": "Your Journal Journey Continues",
                    "message": "Thanks for being a regular user! Consider supporting the project.",
                    "icon": "☕",
                    "actions": ["support", "later"]
                })
    
    return milestones
```

### Voice Recording State Management

#### Recording States
1. **Idle** - Waiting for input
2. **Recording** - Capturing audio (red dot animation)
3. **Processing** - Converting speech to text (spinning animation)
4. **Transcribing** - Whisper is working (progress animation)
5. **Enhancing** - Ollama is processing (if enhanced/structured modes)
6. **Success** - Entry created (checkmark animation)

#### Visual Feedback
```python
# State progression during voice input
states = [
    {"state": "idle", "message": "Hold F8 to record"},
    {"state": "recording", "message": "Recording... Release to stop", "animation": "pulse"},
    {"state": "processing", "message": "Processing audio...", "animation": "spin"},
    {"state": "transcribing", "message": "Converting speech to text...", "animation": "dots"},
    {"state": "enhancing", "message": "Creating enhanced versions...", "animation": "shimmer"},
    {"state": "success", "message": "Entries created!", "animation": "checkmark"}
]
```

### API Endpoints Design

#### Core Entry Management
- `POST /api/entry/create` - Save raw transcription
- `POST /api/entry/process/{entry_id}` - Apply enhancement/structuring
- `GET /api/entry/{entry_id}` - Retrieve single entry
- `GET /api/entries` - List entries with pagination and filters

#### Conversational Interface
- `POST /api/diary/chat` - Process conversational queries
- `GET /api/diary/context/{query}` - Get relevant past entries

#### Pattern Analysis
- `GET /api/patterns/check` - Check if pattern analysis is available
- `POST /api/patterns/analyze` - Trigger pattern detection
- `GET /api/patterns/latest` - Get most recent patterns

#### System Management
- `GET /api/stats` - Entry count, last analysis, etc.
- `POST /api/preferences` - Update user preferences (including Ollama model selection and port)
- `GET /api/preferences` - Get current preferences
- `GET /api/ollama/models` - List available Ollama models
- `POST /api/ollama/test` - Test Ollama connection
- `GET /api/export` - Export data in various formats
- `GET /api/milestones/check` - Check for milestones (7-day usage, 30 entries, etc.)
- `POST /api/milestones/dismiss` - Dismiss a milestone popup

### Key Dependencies & Versions
```python
# requirements.txt
fastapi[standard]==0.115.12
uvicorn[standard]>=0.30.0
pydantic>=2.7.0
sentence-transformers>=3.0.0  # For BGE embeddings
httpx>=0.25.0  # For async HTTP calls to Ollama API
sqlite3  # Built-in
numpy>=1.24.0
python-multipart  # For file uploads
aiofiles  # For async file operations
```

### Ollama Integration via REST API
Instead of using a heavy SDK, we'll communicate with Ollama through its HTTP API:

```python
# Example Ollama API integration
import httpx
from typing import List, Optional

class OllamaService:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
    
    async def list_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return [model["name"] for model in models]
        except:
            return []
    
    async def test_connection(self) -> bool:
        """Test if Ollama is running at the specified URL"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags", timeout=5.0)
                return response.status_code == 200
        except:
            return False
    
    async def process_text(self, text: str, mode: str, model: str = "llama2"):
        """Process text with selected Ollama model"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": self._build_prompt(text, mode),
                    "stream": False
                },
                timeout=30.0
            )
            return response.json()["response"]
```

This approach:
- Keeps the application lightweight (no heavy ML libraries)
- Allows easy model switching through Ollama's model management
- Enables better error handling and timeout control
- Makes it easier to deploy since Ollama runs as a separate service
- Supports custom Ollama ports for flexible deployment

### Performance Considerations

#### Embedding Search Optimization
- For <1000 entries: Brute force search is fine
- For 1000-10000 entries: Implement simple indexing
- Beyond 10000: Consider hierarchical clustering

#### Storage Efficiency
- Compress embeddings using quantization (float32 → int8)
- Store only significant sentences (>10 words)
- Periodic cleanup of redundant patterns

### Privacy & Security Notes
- All processing happens locally
- No external API calls except to local Ollama
- Implement simple encryption for database file
- Clear data export/import for user control

## Memory System (Lightweight Embedding Memory)
- No external vector DB like Faiss or ChromaDB
- All embeddings stored in SQLite
- Entries indexed by topic and timestamp
- When user queries or interacts via "Talk to Your Diary," relevant past entries are fetched using semantic similarity on local embeddings

## Privacy and Distribution
- App remains local by design
- Option to show "Buy me a coffee" pop-up after repeated use to support development
- Users can share the installer, but feature gating may encourage donations

## Nice-to have features 
- **Choose Ollama Model**: Settings page to select which Ollama model to use for text processing
  - Auto-detect available models from Ollama API
  - Option to manually enter custom Ollama port (default: 11434)
  - Test connection button to verify Ollama is running
- **Weekly/Monthly Summaries**: Automatic summarization of entries on a weekly and monthly basis
- **Conversation Prompts**: Gentle prompts in "Talk to Your Diary" mode like:
  - "How are you feeling today?"
  - "What's been on your mind lately?"
  - "Would you like to reflect on this week?"
  - "Tell me about something that made you smile recently"
- **Quick Entry Mode**: Single-click to start recording for rapid thoughts
- **Simple Export**: Export entries to markdown/JSON for data portability

Note: "Talk to Your Diary" improves organically as more entries accumulate, increasing the richness of semantic retrieval and personal insight.

---

This is a mental health-lite, habit-forming journaling experience. Small, simple, powerful. Like a tamagotchi with feelings.
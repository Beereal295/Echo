# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Critical Development Instructions

**NEVER SIMPLIFY APPROACH:**
- If you encounter any technical challenges or blockers, consult with the project lead immediately
- Do NOT change the main architectural approach or simplify implementations without explicit approval
- Maintain the integrity of the documented architecture at all costs
- When stuck, ask for guidance rather than finding workarounds

**Testing and Validation Process:**
1. **Implementation Phase:** Code according to specifications without executing main application
2. **Completion Notification:** Inform project lead when implementation is ready for testing
3. **Testing Phase:** Project lead conducts all testing and validation independently
4. **Confirmation Required:** Wait for explicit confirmation before marking tasks as complete
5. **Iteration:** Address feedback and repeat process until approved

**Development Workflow:**
- Follow the task structure defined in `tasklist.md`
- Never run or test the main application during development
- Focus purely on implementation according to documented specifications
- All testing and validation is handled by project lead
- If we found an error during testing and after fixing the error if the project lead gives a go ahead, fix the errors in the main implementation as well before moving forward

## Project Overview

DearDiary is a local-first journaling application with AI integration via Ollama. The app provides three ways to process journal entries: raw transcription, enhanced style, and structured summaries. Key features include voice-to-text via Whisper, pattern detection after 30 entries, and a conversational "Talk to Your Diary" interface.

## Project Name

- The project is called Echo.

## Tech Stack

- **Backend**: Python with FastAPI
- **Frontend**: React with TypeScript, shadcn/ui components, Tailwind CSS
- **Desktop**: Electron wrapper
- **Database**: SQLite with embeddings stored as JSON
- **AI**: Local Ollama integration via REST API, Whisper for speech-to-text
- **TTS**: Text-to-speech solution for Talk to Your Diary feature (to be finalized)
- **Embeddings**: BGE-small model (384 dimensions) for semantic search

## Architecture

### Core Components

1. **Entry Processing Pipeline**
   - Raw transcription → Enhanced style → Structured summary
   - All three versions stored simultaneously
   - Embeddings generated for semantic search

2. **Memory System**
   - SQLite database with JSON-stored embeddings
   - Semantic similarity search using cosine similarity
   - No external vector database dependencies

3. **AI Integration**
   - Ollama REST API for text processing (no heavy SDK)
   - Configurable models and ports in settings
   - Whisper integration for speech-to-text

### Database Schema

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
    processing_metadata TEXT
)
```

#### Patterns Table
```sql
patterns (
    id INTEGER PRIMARY KEY,
    pattern_type TEXT,  -- 'mood', 'topic', 'behavior', 'temporal'
    description TEXT,
    frequency INTEGER,
    confidence REAL,
    first_seen DATE,
    last_seen DATE,
    related_entries TEXT  -- JSON array of entry IDs
)
```

## Key API Endpoints

- `POST /api/entry/create` - Save raw transcription
- `POST /api/entry/process/{entry_id}` - Apply enhancement/structuring
- `POST /api/diary/chat` - Process conversational queries
- `GET /api/patterns/check` - Check if pattern analysis is available
- `POST /api/patterns/analyze` - Trigger pattern detection
- `GET /api/ollama/models` - List available Ollama models
- `POST /api/ollama/test` - Test Ollama connection
- `GET /api/milestones/check` - Check for milestones (7-day usage, 30 entries)

## LLM Prompts

### Enhanced Style Mode
```json
{
  "system": "You are a helpful writing assistant. Improve the grammar, punctuation, and flow of personal journal entries. Keep the original tone and intent. Do not remove slang or informal expressions unless absolutely necessary. Keep it personal and natural.",
  "prompt": "{raw_journal_text}"
}
```

### Structured Summary Mode
```json
{
  "system": "You are a personal journal assistant. Summarize diary entries into a few short, structured paragraphs. Identify key topics, emotions, or events. Use warm, human language. Do not rewrite everything—just organize the main ideas clearly.",
  "prompt": "{raw_journal_text}"
}
```

### Talk to Your Diary
```json
{
  "system": "You are a reflective journal companion. Use the user's past journal entries to answer their question. Speak gently, and do not offer advice. Reflect on what they've already shared or summarize their experiences.",
  "prompt": "Past entries:\n{retrieved_text}\n\nUser asked: {user_query}"
}
```

## Frontend Architecture

### Layout Structure
- Persistent left sidebar (Notion-style) with navigation
- Main content area for pages
- Floating plus button for quick entry creation
- Split-view for entry browsing (list + detail)

### Key Features
- Pattern Insights (unlocked after 30 entries) - Diamond icon in sidebar
- Voice recording with global hotkey support (default F8)
- Milestone celebrations (pattern unlock, buy-me-coffee after 7 days)
- Three-mode entry display (raw, enhanced, structured with color coding)

### State Management
Recording states: idle → recording → processing → transcribing → enhancing → success

## Current Status

This appears to be a planning/design phase project with comprehensive documentation but minimal implementation. The codebase currently contains only documentation files in the `Documentation/` folder:
- `diary-project-updated.md` - Full technical specification
- `journal-frontend-doc.md` - Frontend implementation guide  
- `journal-user-flow.md` - User experience design
- `prompt_spec_journal_ai.md` - AI prompt specifications

No actual code files (Python, JavaScript, etc.) exist yet in the repository.

## Development Notes

- For technical implementation check context7 MCP for latest documentation before coding
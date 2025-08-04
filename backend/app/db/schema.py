"""Database schema definitions"""

# Entries table
ENTRIES_TABLE = """
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_text TEXT NOT NULL,
    enhanced_text TEXT,
    structured_summary TEXT,
    mode TEXT NOT NULL DEFAULT 'raw',
    embeddings TEXT,  -- JSON array of floats
    timestamp DATETIME NOT NULL,
    mood_tags TEXT,   -- JSON array of strings
    word_count INTEGER DEFAULT 0,
    processing_metadata TEXT  -- JSON object
)
"""

# Patterns table
PATTERNS_TABLE = """
CREATE TABLE IF NOT EXISTS patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type TEXT NOT NULL,  -- 'mood', 'topic', 'behavior', 'temporal'
    description TEXT NOT NULL,
    frequency INTEGER DEFAULT 0,
    confidence REAL DEFAULT 0.0,
    first_seen DATE,
    last_seen DATE,
    related_entries TEXT,  -- JSON array of entry IDs
    keywords TEXT  -- JSON array of keywords
)
"""

# Preferences table
PREFERENCES_TABLE = """
CREATE TABLE IF NOT EXISTS preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    value_type TEXT DEFAULT 'string',  -- string, int, float, bool, json
    description TEXT
)
"""

# Drafts table for auto-save
DRAFTS_TABLE = """
CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    metadata TEXT,  -- JSON object
    created_at DATETIME NOT NULL,
    updated_at DATETIME
)
"""

# Conversations table for Talk to Your Diary feature
CONVERSATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    duration INTEGER DEFAULT 0,  -- in seconds
    transcription TEXT NOT NULL,
    conversation_type TEXT NOT NULL,  -- 'call' or 'chat'
    message_count INTEGER DEFAULT 0,
    search_queries_used TEXT,  -- JSON array
    created_at DATETIME NOT NULL,
    updated_at DATETIME
)
"""

# Schema version table for migrations
SCHEMA_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME NOT NULL,
    description TEXT
)
"""

# Indexes for better performance
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_entries_timestamp ON entries(timestamp DESC)",
    "CREATE INDEX IF NOT EXISTS idx_entries_mode ON entries(mode)",
    "CREATE INDEX IF NOT EXISTS idx_entries_mood_tags ON entries(mood_tags)",
    "CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns(pattern_type)",
    "CREATE INDEX IF NOT EXISTS idx_patterns_confidence ON patterns(confidence DESC)",
    "CREATE INDEX IF NOT EXISTS idx_preferences_key ON preferences(key)",
    "CREATE INDEX IF NOT EXISTS idx_drafts_updated ON drafts(updated_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp DESC)",
    "CREATE INDEX IF NOT EXISTS idx_conversations_type ON conversations(conversation_type)"
]

# All tables in order of creation
ALL_TABLES = [
    SCHEMA_VERSION_TABLE,
    ENTRIES_TABLE,
    PATTERNS_TABLE,
    PREFERENCES_TABLE,
    DRAFTS_TABLE,
    CONVERSATIONS_TABLE
]
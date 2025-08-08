"""Database migration system"""
from datetime import datetime
from typing import List, Tuple


# Migration format: (version, description, up_sql, down_sql)
MIGRATIONS: List[Tuple[int, str, str, str]] = [
    (
        1,
        "Initial schema",
        """-- This migration is handled by schema.py create_tables()""",
        """-- Rollback not supported for initial schema"""
    ),
    (
        2,
        "Add keywords column to patterns table",
        """ALTER TABLE patterns ADD COLUMN keywords TEXT""",
        """ALTER TABLE patterns DROP COLUMN keywords"""
    ),
    (
        3,
        "Add conversations table for Talk to Your Diary feature",
        """CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    duration INTEGER DEFAULT 0,
    transcription TEXT NOT NULL,
    conversation_type TEXT NOT NULL,
    message_count INTEGER DEFAULT 0,
    search_queries_used TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_type ON conversations(conversation_type);""",
        """DROP TABLE IF EXISTS conversations;"""
    ),
    (
        4,
        "Add smart_tags column to entries table",
        """ALTER TABLE entries ADD COLUMN smart_tags TEXT;
CREATE INDEX IF NOT EXISTS idx_entries_smart_tags ON entries(smart_tags);""",
        """DROP INDEX IF EXISTS idx_entries_smart_tags;
ALTER TABLE entries DROP COLUMN smart_tags;"""
    ),
    (
        5,
        "Add advanced memory scoring fields",
        """-- Add new scoring fields to agent_memories
ALTER TABLE agent_memories ADD COLUMN base_importance_score REAL DEFAULT 5.0;
ALTER TABLE agent_memories ADD COLUMN llm_importance_score REAL;
ALTER TABLE agent_memories ADD COLUMN user_score_adjustment REAL DEFAULT 0;
ALTER TABLE agent_memories ADD COLUMN final_importance_score REAL DEFAULT 5.0;
ALTER TABLE agent_memories ADD COLUMN user_rated INTEGER DEFAULT 0;
ALTER TABLE agent_memories ADD COLUMN score_source TEXT DEFAULT 'rule';
ALTER TABLE agent_memories ADD COLUMN llm_processed INTEGER DEFAULT 0;
ALTER TABLE agent_memories ADD COLUMN llm_processed_at DATETIME;
ALTER TABLE agent_memories ADD COLUMN user_rated_at DATETIME;
ALTER TABLE agent_memories ADD COLUMN decay_last_calculated DATETIME;
ALTER TABLE agent_memories ADD COLUMN effective_score_cache REAL;
ALTER TABLE agent_memories ADD COLUMN score_breakdown TEXT;
ALTER TABLE agent_memories ADD COLUMN marked_for_deletion INTEGER DEFAULT 0;
ALTER TABLE agent_memories ADD COLUMN marked_for_deletion_at DATETIME;
ALTER TABLE agent_memories ADD COLUMN deletion_reason TEXT;
ALTER TABLE agent_memories ADD COLUMN archived INTEGER DEFAULT 0;
ALTER TABLE agent_memories ADD COLUMN archived_at DATETIME;

-- Create indexes for new fields
CREATE INDEX IF NOT EXISTS idx_memory_user_rated ON agent_memories(user_rated);
CREATE INDEX IF NOT EXISTS idx_memory_llm_processed ON agent_memories(llm_processed);
CREATE INDEX IF NOT EXISTS idx_memory_final_score ON agent_memories(final_importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_memory_marked_deletion ON agent_memories(marked_for_deletion);
CREATE INDEX IF NOT EXISTS idx_memory_archived ON agent_memories(archived);""",
        """-- Rollback: Drop indexes and columns
DROP INDEX IF EXISTS idx_memory_user_rated;
DROP INDEX IF EXISTS idx_memory_llm_processed;
DROP INDEX IF EXISTS idx_memory_final_score;
DROP INDEX IF EXISTS idx_memory_marked_deletion;
DROP INDEX IF EXISTS idx_memory_archived;"""
    ),
]


async def get_current_version(db) -> int:
    """Get current schema version"""
    try:
        result = await db.fetch_one(
            "SELECT MAX(version) as version FROM schema_version"
        )
        return result["version"] if result and result["version"] else 0
    except:
        # Table doesn't exist yet
        return 0


async def apply_migration(db, version: int, description: str, up_sql: str):
    """Apply a single migration"""
    if up_sql.strip() and not up_sql.strip().startswith("--"):
        # Split multiple statements by semicolon and execute each one
        statements = [stmt.strip() for stmt in up_sql.split(';') if stmt.strip()]
        for statement in statements:
            await db.execute(statement)
    
    await db.execute(
        "INSERT INTO schema_version (version, applied_at, description) VALUES (?, ?, ?)",
        (version, datetime.now().isoformat(), description)
    )
    await db.commit()
    print(f"Applied migration {version}: {description}")


async def run_migrations(db):
    """Run all pending migrations"""
    current_version = await get_current_version(db)
    
    for version, description, up_sql, _ in MIGRATIONS:
        if version > current_version:
            await apply_migration(db, version, description, up_sql)
    
    final_version = await get_current_version(db)
    if final_version > current_version:
        print(f"Database migrated from version {current_version} to {final_version}")
    else:
        print(f"Database is up to date at version {final_version}")
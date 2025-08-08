#!/usr/bin/env python3
"""
Fix memory columns migration
"""
import sqlite3
from pathlib import Path

def add_missing_columns():
    """Add missing columns to agent_memories table"""
    
    db_path = Path(__file__).parent / "echo.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get current columns
    cursor.execute("PRAGMA table_info(agent_memories)")
    existing_columns = [column[1] for column in cursor.fetchall()]
    
    # Define new columns to add
    new_columns = [
        ("base_importance_score", "REAL DEFAULT 5.0"),
        ("llm_importance_score", "REAL"),
        ("user_score_adjustment", "REAL DEFAULT 0"),
        ("final_importance_score", "REAL DEFAULT 5.0"),
        ("user_rated", "INTEGER DEFAULT 0"),
        ("score_source", "TEXT DEFAULT 'rule'"),
        ("llm_processed", "INTEGER DEFAULT 0"),
        ("llm_processed_at", "DATETIME"),
        ("user_rated_at", "DATETIME"),
        ("decay_last_calculated", "DATETIME"),
        ("effective_score_cache", "REAL"),
        ("score_breakdown", "TEXT"),
        ("marked_for_deletion", "INTEGER DEFAULT 0"),
        ("marked_for_deletion_at", "DATETIME"),
        ("deletion_reason", "TEXT"),
        ("archived", "INTEGER DEFAULT 0"),
        ("archived_at", "DATETIME")
    ]
    
    # Add missing columns
    added_columns = []
    for col_name, col_def in new_columns:
        if col_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE agent_memories ADD COLUMN {col_name} {col_def}")
                added_columns.append(col_name)
                print(f"Added column: {col_name}")
            except Exception as e:
                print(f"Failed to add {col_name}: {e}")
    
    # Add indexes
    indexes = [
        ("idx_memory_user_rated", "agent_memories(user_rated)"),
        ("idx_memory_llm_processed", "agent_memories(llm_processed)"),
        ("idx_memory_final_score", "agent_memories(final_importance_score DESC)"),
        ("idx_memory_marked_deletion", "agent_memories(marked_for_deletion)"),
        ("idx_memory_archived", "agent_memories(archived)")
    ]
    
    for idx_name, idx_def in indexes:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_def}")
            print(f"Created index: {idx_name}")
        except Exception as e:
            print(f"Failed to create index {idx_name}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"Successfully added {len(added_columns)} columns and created indexes")
    return len(added_columns) > 0

if __name__ == "__main__":
    success = add_missing_columns()
    if success:
        print("Migration completed successfully!")
    else:
        print("No columns needed to be added.")
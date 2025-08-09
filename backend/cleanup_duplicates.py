#!/usr/bin/env python3
"""
Emergency cleanup script to remove duplicate entries created by the broken memory recreation script.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from app.db.database import db

async def cleanup_duplicate_entries():
    """Remove duplicate entries created by the broken script"""
    
    # Set database path
    db.db_path = str(Path(__file__).parent / "echo.db")
    await db.connect()
    
    try:
        # Find entries created today with high IDs (likely duplicates)
        duplicates = await db.fetch_all("""
            SELECT id, raw_text, timestamp 
            FROM entries 
            WHERE id >= 2568
            ORDER BY id DESC
        """)
        
        if not duplicates:
            print("✓ No duplicate entries found")
            return
        
        print(f"Found {len(duplicates)} potential duplicate entries (IDs 2568+)")
        print("\nFirst few duplicates:")
        for dup in duplicates[:5]:
            print(f"  ID {dup['id']}: {dup['raw_text'][:50]}... ({dup['timestamp']})")
        
        confirm = input(f"\nDelete {len(duplicates)} duplicate entries? Type 'YES' to confirm: ").strip()
        
        if confirm != 'YES':
            print("Cancelled")
            return
        
        # Delete duplicates
        duplicate_ids = [dup['id'] for dup in duplicates]
        placeholders = ','.join(['?'] * len(duplicate_ids))
        
        await db.execute(f"DELETE FROM entries WHERE id IN ({placeholders})", duplicate_ids)
        await db.commit()
        
        print(f"✓ Deleted {len(duplicates)} duplicate entries")
        
        # Also clean up any memories from these entries
        memory_result = await db.execute(f"""
            DELETE FROM agent_memories 
            WHERE related_entry_id IN ({placeholders})
        """, duplicate_ids)
        await db.commit()
        
        deleted_memories = memory_result.rowcount if hasattr(memory_result, 'rowcount') else 0
        print(f"✓ Deleted {deleted_memories} memories from duplicate entries")
        
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(cleanup_duplicate_entries())
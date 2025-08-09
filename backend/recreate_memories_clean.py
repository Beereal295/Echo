#!/usr/bin/env python3
"""
Clean script to recreate memories for existing entries and conversations.
Uses EXACT main app pipeline: Extract → Score → Embed
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from app.db.database import db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def recreate_all_memories():
    """Recreate memories for all existing entries and conversations"""
    
    print("=" * 60)
    print("RECREATE MEMORIES - CLEAN PIPELINE")
    print("=" * 60)
    print("Uses EXACT main app functions:")
    print("- _extract_entry_memories() for entries")
    print("- extract_memories_with_llm() + store_memory() for conversations")
    print("- Automatic Extract → Score → Embed pipeline")
    
    # Get counts
    entry_count = await db.fetch_one("SELECT COUNT(*) as count FROM entries")
    conv_count = await db.fetch_one("SELECT COUNT(*) as count FROM conversations")
    memory_count = await db.fetch_one("SELECT COUNT(*) as count FROM agent_memories WHERE is_active = 1")
    
    total_entries = entry_count['count'] if entry_count else 0
    total_conversations = conv_count['count'] if conv_count else 0
    existing_memories = memory_count['count'] if memory_count else 0
    
    print(f"\nCurrent database state:")
    print(f"- {total_entries} entries")
    print(f"- {total_conversations} conversations") 
    print(f"- {existing_memories} existing memories")
    
    input("\nPress Enter to start recreating memories...")
    
    # Step 1: Delete existing memories
    print("\n🗑️ Step 1: Clearing existing memories...")
    await db.execute("DELETE FROM agent_memories")
    await db.commit()
    print("✓ All memories deleted")
    
    # Step 2: Reset processing flags
    print("\n🔄 Step 2: Resetting processing flags...")
    await db.execute("""
        UPDATE entries 
        SET memory_extracted = 0, memory_extracted_llm = 0, memory_extracted_at = NULL
    """)
    await db.execute("""
        UPDATE conversations 
        SET memory_extracted = 0, memory_extracted_llm = 0, memory_extracted_at = NULL
    """)
    await db.commit()
    print("✓ All processing flags reset")
    
    # Step 3: Process entries with main app function
    print(f"\n🚀 Step 3: Processing {total_entries} entries...")
    entries = await db.fetch_all("SELECT id FROM entries ORDER BY timestamp DESC")
    
    processed = 0
    for entry in entries:
        try:
            # Use EXACT main app function
            from app.api.routes.entries import _extract_entry_memories
            await _extract_entry_memories(entry['id'])
            
            processed += 1
            if processed % 10 == 0:
                print(f"  ✓ Processed {processed}/{total_entries} entries...")
                await asyncio.sleep(1)  # Prevent database locks
                
        except Exception as e:
            logger.error(f"Failed to process entry {entry['id']}: {e}")
    
    print(f"✅ Completed {processed} entries")
    
    # Step 4: Process conversations with memory service
    print(f"\n🚀 Step 4: Processing {total_conversations} conversations...")
    conversations = await db.fetch_all("SELECT id, transcription FROM conversations WHERE transcription IS NOT NULL AND transcription != ''")
    
    processed = 0
    for conv in conversations:
        try:
            from app.services.memory_service import MemoryService
            memory_service = MemoryService()
            
            # Extract memories using LLM
            memories = await memory_service.extract_memories_with_llm(
                text=conv['transcription'],
                source_id=conv['id'],
                source_type='conversation'
            )
            
            # Store memories (triggers automatic Score → Embed)
            stored = 0
            for memory in memories:
                try:
                    await memory_service.store_memory(memory)
                    stored += 1
                except Exception as e:
                    logger.error(f"Failed to store memory: {e}")
            
            # Mark as processed
            await db.execute("""
                UPDATE conversations 
                SET memory_extracted = 1, memory_extracted_llm = 1, memory_extracted_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (conv['id'],))
            await db.commit()
            
            processed += 1
            logger.info(f"Stored {stored} memories from conversation {conv['id']}")
            
            if processed % 5 == 0:
                print(f"  ✓ Processed {processed}/{len(conversations)} conversations...")
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Failed to process conversation {conv['id']}: {e}")
    
    print(f"✅ Completed {processed} conversations")
    
    # Step 5: Wait for async scoring and embedding
    print("\n⏳ Step 5: Waiting for async scoring and embedding...")
    print("Background tasks are processing Extract → Score → Embed pipeline...")
    await asyncio.sleep(30)
    
    # Step 6: Final statistics
    print("\n📊 Step 6: Final results...")
    final_stats = await db.fetch_one("""
        SELECT 
            COUNT(*) as total_memories,
            SUM(CASE WHEN score_source = 'llm_extraction' THEN 1 ELSE 0 END) as being_scored,
            SUM(CASE WHEN score_source = 'llm' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN embedding IS NOT NULL THEN 1 ELSE 0 END) as embedded
        FROM agent_memories 
        WHERE is_active = 1
    """)
    
    print(f"✅ Memory Recreation Results:")
    print(f"- Total memories created: {final_stats['total_memories']}")
    print(f"- Being scored: {final_stats['being_scored']}")
    print(f"- Fully processed: {final_stats['completed']}")
    print(f"- With embeddings: {final_stats['embedded']}")
    
    print("\n" + "=" * 60)
    print("🎉 MEMORY RECREATION COMPLETE!")
    print("All memories recreated using main app pipeline")
    print("=" * 60)


async def main():
    """Main function"""
    
    # Set database path
    db.db_path = str(Path(__file__).parent / "echo.db")
    print(f"Using database: {db.db_path}")
    
    # Connect to database
    await db.connect()
    
    try:
        await recreate_all_memories()
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
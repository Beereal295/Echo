"""
Script to reprocess existing entries and conversations with LLM memory extraction.
This will extract higher quality memories using LLM instead of rule-based extraction.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional
import aiohttp

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from app.db.database import db
from app.services.memory_service import MemoryService
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def reprocess_conversations(batch_size: int = 5, limit: Optional[int] = None):
    """Reprocess conversations that haven't been processed with LLM yet"""
    memory_service = MemoryService()
    
    # Get unprocessed conversations
    query = """
        SELECT id, transcription 
        FROM conversations 
        WHERE (memory_extracted_llm IS NULL OR memory_extracted_llm = 0)
        AND transcription IS NOT NULL
        AND transcription != ''
        ORDER BY created_at DESC
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    conversations = await db.fetch_all(query)
    
    if not conversations:
        logger.info("No unprocessed conversations found")
        return 0
    
    logger.info(f"Found {len(conversations)} conversations to process with LLM")
    
    total_memories = 0
    processed = 0
    
    for conversation in conversations:
        try:
            logger.info(f"Processing conversation {conversation['id']}...")
            
            # FIRST: Deactivate old rule-based memories from this conversation
            deactivated = await db.execute("""
                UPDATE agent_memories 
                SET is_active = 0
                WHERE source_conversation_id = ? 
                AND score_source = 'rule'
                AND user_rated = 0
            """, (conversation['id'],))
            await db.commit()
            deactivated_count = deactivated.rowcount if hasattr(deactivated, 'rowcount') else 0
            logger.info(f"Deactivated {deactivated_count} old rule-based memories from conversation {conversation['id']}")
            
            # THEN: Extract memories using LLM
            memories = await memory_service.extract_memories_with_llm(
                text=conversation['transcription'],
                source_id=conversation['id'],
                source_type='conversation'
            )
            
            # Store new LLM memories
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
                SET memory_extracted_llm = 1,
                    memory_extracted_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (conversation['id'],))
            await db.commit()
            
            logger.info(f"✓ Conversation {conversation['id']}: extracted {stored} memories")
            total_memories += stored
            processed += 1
            
            # Small delay between batches
            if processed % batch_size == 0:
                logger.info(f"Processed {processed} conversations, waiting 2 seconds...")
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Failed to process conversation {conversation['id']}: {e}")
    
    logger.info(f"Completed: Processed {processed} conversations, extracted {total_memories} memories")
    return total_memories


async def reprocess_entries(batch_size: int = 5, limit: Optional[int] = None):
    """Reprocess entries that haven't been processed with LLM yet"""
    memory_service = MemoryService()
    
    # Get unprocessed entries (prefer enhanced text)
    query = """
        SELECT id, enhanced_text, raw_text 
        FROM entries 
        WHERE (memory_extracted_llm IS NULL OR memory_extracted_llm = 0)
        AND (enhanced_text IS NOT NULL OR raw_text IS NOT NULL)
        ORDER BY timestamp DESC
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    entries = await db.fetch_all(query)
    
    if not entries:
        logger.info("No unprocessed entries found")
        return 0
    
    logger.info(f"Found {len(entries)} entries to process with LLM")
    
    total_memories = 0
    processed = 0
    
    for entry in entries:
        try:
            # Use enhanced text if available, otherwise raw
            text = entry['enhanced_text'] or entry['raw_text']
            if not text or not text.strip():
                continue
            
            logger.info(f"Processing entry {entry['id']}...")
            
            # FIRST: Deactivate old rule-based memories from this entry
            deactivated = await db.execute("""
                UPDATE agent_memories 
                SET is_active = 0
                WHERE related_entry_id = ? 
                AND score_source = 'rule'
                AND user_rated = 0
            """, (entry['id'],))
            await db.commit()
            deactivated_count = deactivated.rowcount if hasattr(deactivated, 'rowcount') else 0
            logger.info(f"Deactivated {deactivated_count} old rule-based memories from entry {entry['id']}")
            
            # THEN: Extract memories using LLM
            memories = await memory_service.extract_memories_with_llm(
                text=text,
                source_id=entry['id'],
                source_type='entry'
            )
            
            # Store new LLM memories
            stored = 0
            for memory in memories:
                try:
                    await memory_service.store_memory(memory)
                    stored += 1
                except Exception as e:
                    logger.error(f"Failed to store memory: {e}")
            
            # Mark as processed
            await db.execute("""
                UPDATE entries 
                SET memory_extracted_llm = 1,
                    memory_extracted_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (entry['id'],))
            await db.commit()
            
            logger.info(f"✓ Entry {entry['id']}: extracted {stored} memories")
            total_memories += stored
            processed += 1
            
            # Small delay between batches
            if processed % batch_size == 0:
                logger.info(f"Processed {processed} entries, waiting 2 seconds...")
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Failed to process entry {entry['id']}: {e}")
    
    logger.info(f"Completed: Processed {processed} entries, extracted {total_memories} memories")
    return total_memories


async def clean_duplicate_memories():
    """Clean up duplicate memories after LLM extraction"""
    logger.info("Checking for duplicate memories...")
    
    # Find exact duplicates
    duplicates = await db.fetch_all("""
        SELECT content, COUNT(*) as count, GROUP_CONCAT(id) as ids
        FROM agent_memories
        WHERE is_active = 1
        GROUP BY content
        HAVING COUNT(*) > 1
    """)
    
    if not duplicates:
        logger.info("No duplicate memories found")
        return 0
    
    logger.info(f"Found {len(duplicates)} groups of duplicate memories")
    
    removed = 0
    for dup in duplicates:
        ids = [int(id_str) for id_str in dup['ids'].split(',')]
        # Keep the first one (oldest), deactivate others
        to_remove = ids[1:]
        
        if to_remove:
            placeholders = ','.join(['?'] * len(to_remove))
            await db.execute(f"""
                UPDATE agent_memories
                SET is_active = 0
                WHERE id IN ({placeholders})
            """, to_remove)
            
            removed += len(to_remove)
            logger.info(f"Deactivated {len(to_remove)} duplicates of: {dup['content'][:50]}...")
    
    await db.commit()
    logger.info(f"Deactivated {removed} duplicate memories")
    return removed


async def reset_processing_flags():
    """Reset memory_extracted_llm flags to allow reprocessing"""
    logger.info("Resetting LLM processing flags...")
    
    # Reset conversation flags
    conv_result = await db.execute("""
        UPDATE conversations 
        SET memory_extracted_llm = 0,
            memory_extracted_at = NULL
        WHERE memory_extracted_llm = 1
    """)
    await db.commit()
    conv_count = conv_result.rowcount if hasattr(conv_result, 'rowcount') else 0
    logger.info(f"Reset {conv_count} conversation processing flags")
    
    # Reset entry flags
    entry_result = await db.execute("""
        UPDATE entries 
        SET memory_extracted_llm = 0,
            memory_extracted_at = NULL
        WHERE memory_extracted_llm = 1
    """)
    await db.commit()
    entry_count = entry_result.rowcount if hasattr(entry_result, 'rowcount') else 0
    logger.info(f"Reset {entry_count} entry processing flags")
    
    total_reset = conv_count + entry_count
    print(f"\n✓ Reset processing flags for {conv_count} conversations and {entry_count} entries")
    print(f"✓ Total items now available for reprocessing: {total_reset}")
    
    return total_reset


async def delete_rule_based_memories():
    """Delete all rule-based memories from the database"""
    logger.info("Deleting all rule-based memories...")
    
    # First, count how many will be deleted
    count_result = await db.fetch_one("""
        SELECT COUNT(*) as count 
        FROM agent_memories 
        WHERE score_source = 'rule'
    """)
    total_count = count_result['count'] if count_result else 0
    
    if total_count == 0:
        print("\n✓ No rule-based memories found to delete")
        return 0
    
    # Ask for confirmation
    print(f"\n⚠️  WARNING: This will permanently delete {total_count} rule-based memories!")
    print("This action cannot be undone.")
    confirm = input("Are you sure you want to proceed? (type 'DELETE' to confirm): ").strip()
    
    if confirm != 'DELETE':
        print("❌ Deletion cancelled")
        return 0
    
    # Delete rule-based memories
    delete_result = await db.execute("""
        DELETE FROM agent_memories 
        WHERE score_source = 'rule'
    """)
    await db.commit()
    
    deleted_count = delete_result.rowcount if hasattr(delete_result, 'rowcount') else 0
    logger.info(f"Deleted {deleted_count} rule-based memories")
    
    print(f"\n✓ Successfully deleted {deleted_count} rule-based memories")
    print("✓ Database cleanup completed")
    
    return deleted_count


async def clear_all_memories_and_recreate_with_main_pipeline():
    """Delete ALL memories and recreate using EXACT main app pipeline functions"""
    print("\n" + "=" * 60)
    print("CLEAR ALL MEMORIES AND RECREATE WITH MAIN PIPELINE")
    print("=" * 60)
    print("\nThis will:")
    print("1. Delete ALL existing memories")
    print("2. Reset all processing flags")
    print("3. Use EXACT main app functions: _extract_entry_memories() and store_memory()")
    print("4. Automatic Extract → Score → Embed pipeline")
    
    # Count existing memories
    memory_stats = await db.fetch_one("""
        SELECT COUNT(*) as total FROM agent_memories WHERE is_active = 1
    """)
    
    # Get entry and conversation counts
    entry_count = await db.fetch_one("SELECT COUNT(*) as count FROM entries")
    conv_count = await db.fetch_one("SELECT COUNT(*) as count FROM conversations")
    
    total_memories = memory_stats['total'] if memory_stats else 0
    total_entries = entry_count['count'] if entry_count else 0
    total_conversations = conv_count['count'] if conv_count else 0
    
    print(f"\nCurrent state:")
    print(f"  - {total_memories} existing memories")
    print(f"  - {total_entries} entries to process")
    print(f"  - {total_conversations} conversations to process")
    
    # Simple confirmation
    input("\nPress Enter to continue or Ctrl+C to cancel...")
    print("🚀 Starting memory recreation...")
    
    # Step 1: Delete all existing memories
    print("\n🗑️  Step 1: Deleting all existing memories...")
    delete_result = await db.execute("DELETE FROM agent_memories")
    await db.commit()
    deleted_count = delete_result.rowcount if hasattr(delete_result, 'rowcount') else 0
    print(f"✓ Deleted {deleted_count} memories")
    
    # Step 2: Reset all processing flags
    print("\n🔄 Step 2: Resetting all processing flags...")
    await db.execute("""
        UPDATE entries 
        SET memory_extracted = 0, memory_extracted_llm = 0, memory_extracted_at = NULL
    """)
    await db.execute("""
        UPDATE conversations 
        SET memory_extracted = 0, memory_extracted_llm = 0, memory_extracted_at = NULL
    """)
    await db.commit()
    print("✓ Reset all processing flags")
    
    # Step 3: Process entries using EXACT main app function
    print("\n🚀 Step 3: Processing entries with main app functions...")
    entries = await db.fetch_all("SELECT id FROM entries ORDER BY timestamp DESC")
    
    processed_entries = 0
    for entry in entries:
        try:
            # Use the EXACT same function as the main application
            from app.api.routes.entries import _extract_entry_memories
            await _extract_entry_memories(entry['id'])
            
            processed_entries += 1
            if processed_entries % 10 == 0:
                print(f"  Processed {processed_entries}/{total_entries} entries...")
                await asyncio.sleep(2)  # Prevent database locks
            
        except Exception as e:
            logger.error(f"Error processing entry {entry['id']}: {e}")
    
    print(f"✓ Processed {processed_entries} entries")
    
    # Step 4: Process conversations using memory service
    print(f"\n🚀 Step 4: Processing conversations...")
    conversations = await db.fetch_all("SELECT id, transcription FROM conversations ORDER BY created_at DESC")
    
    processed_conversations = 0
    for conversation in conversations:
        if not conversation['transcription'] or not conversation['transcription'].strip():
            continue
            
        try:
            from app.services.memory_service import MemoryService
            memory_service = MemoryService()
            
            # Extract memories using LLM (same as main app)
            memories = await memory_service.extract_memories_with_llm(
                text=conversation['transcription'],
                source_id=conversation['id'],
                source_type='conversation'
            )
            
            # Store each memory (triggers automatic Score → Embed pipeline)
            stored_count = 0
            for memory in memories:
                try:
                    await memory_service.store_memory(memory)
                    stored_count += 1
                except Exception as e:
                    logger.error(f"Failed to store memory: {e}")
            
            # Mark conversation as processed
            await db.execute("""
                UPDATE conversations 
                SET memory_extracted = 1,
                    memory_extracted_llm = 1,
                    memory_extracted_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (conversation['id'],))
            await db.commit()
            
            processed_conversations += 1
            logger.info(f"LLM extracted and stored {stored_count} memories from conversation {conversation['id']}")
            
            if processed_conversations % 5 == 0:
                print(f"  Processed {processed_conversations}/{total_conversations} conversations...")
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Error processing conversation {conversation['id']}: {e}")
    
    print(f"✓ Processed {processed_conversations} conversations")
    
    # Step 5: Wait for async scoring and embedding to complete
    print("\n⏳ Step 5: Waiting for async scoring and embedding to complete...")
    print("This may take several minutes as memories are scored and embedded...")
    await asyncio.sleep(60)  # Give time for async processing
    
    # Step 6: Show final statistics
    print("\n📊 Step 6: Final statistics...")
    await show_statistics()
    
    print("\n" + "=" * 60)
    print("✅ MEMORY RECREATION COMPLETED!")
    print("All memories recreated using exact main app pipeline.")
    print("=" * 60)


async def clear_all_memories_and_recreate_with_main_pipeline_BROKEN():
    """Delete ALL memories and recreate using main app pipeline via API calls"""
    print("\n" + "=" * 60)
    print("CLEAR ALL MEMORIES AND RECREATE WITH MAIN PIPELINE")
    print("=" * 60)
    print("\nThis will:")
    print("1. Delete ALL existing memories (rule-based AND LLM)")
    print("2. Reset all processing flags")
    print("3. Recreate memories using the EXACT main app pipeline via API calls")
    print("4. This uses the same pipeline that successfully worked in our test\n")
    
    # Count existing memories
    memory_stats = await db.fetch_one("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN score_source = 'rule' THEN 1 ELSE 0 END) as rule_based,
            SUM(CASE WHEN score_source = 'llm' THEN 1 ELSE 0 END) as llm_based,
            SUM(CASE WHEN score_source = 'llm_extraction' THEN 1 ELSE 0 END) as llm_extraction
        FROM agent_memories 
        WHERE is_active = 1
    """)
    
    total = memory_stats['total'] if memory_stats else 0
    if total == 0:
        print("✓ No existing memories found")
    else:
        print(f"Found {total} existing memories:")
        print(f"  - Rule-based: {memory_stats['rule_based'] or 0}")
        print(f"  - LLM scored: {memory_stats['llm_based'] or 0}")
        print(f"  - LLM extraction: {memory_stats['llm_extraction'] or 0}")
    
    # Get entry and conversation counts
    entry_count = await db.fetch_one("SELECT COUNT(*) as count FROM entries")
    conv_count = await db.fetch_one("SELECT COUNT(*) as count FROM conversations")
    
    total_entries = entry_count['count'] if entry_count else 0
    total_conversations = conv_count['count'] if conv_count else 0
    
    print(f"\nWill recreate memories for:")
    print(f"  - {total_entries} entries")
    print(f"  - {total_conversations} conversations")
    
    # Simple confirmation
    print(f"\n⚠️  WARNING: This will delete {total} existing memories and recreate from scratch!")
    print("This action cannot be undone and will take some time.")
    input("\nPress Enter to continue or Ctrl+C to cancel...")
    print("🚀 Starting memory recreation...")
    
    # Step 1: Delete all existing memories
    print("\n🗑️  Step 1: Deleting all existing memories...")
    delete_result = await db.execute("DELETE FROM agent_memories")
    await db.commit()
    deleted_count = delete_result.rowcount if hasattr(delete_result, 'rowcount') else 0
    print(f"✓ Deleted {deleted_count} memories")
    
    # Step 2: Reset all processing flags
    print("\n🔄 Step 2: Resetting all processing flags...")
    await db.execute("""
        UPDATE entries 
        SET memory_extracted = 0, memory_extracted_llm = 0, memory_extracted_at = NULL
    """)
    await db.execute("""
        UPDATE conversations 
        SET memory_extracted = 0, memory_extracted_llm = 0, memory_extracted_at = NULL
    """)
    await db.commit()
    print("✓ Reset all processing flags")
    
    # Step 3: Ready to process
    print("\n🚀 Step 3: Ready to process with main pipeline functions...")
    
    # Step 4: Recreate memories using main pipeline - DIRECTLY call memory extraction
    print("\n🚀 Step 4: Recreating memories using main app pipeline...")
    
    # Process entries by triggering memory extraction directly on existing entries
    print(f"Processing {total_entries} entries...")
    entries = await db.fetch_all("SELECT id FROM entries ORDER BY timestamp DESC")
    
    processed_entries = 0
    for entry in entries:
        try:
            # Use the EXACT same function as the main application
            from app.api.routes.entries import _extract_entry_memories
            await _extract_entry_memories(entry['id'])
            
            processed_entries += 1
            if processed_entries % 10 == 0:
                print(f"  Processed {processed_entries}/{total_entries} entries...")
                await asyncio.sleep(2)  # Prevent database locks
            
        except Exception as e:
            logger.error(f"Error processing entry {entry['id']}: {e}")
    
    print(f"✓ Processed {processed_entries} entries")
        
        # Process conversations directly using memory service
        print(f"\nProcessing {total_conversations} conversations...")
        conversations = await db.fetch_all("SELECT id, transcription FROM conversations ORDER BY created_at DESC")
        
        processed_conversations = 0
        for conversation in conversations:
            if not conversation['transcription'] or not conversation['transcription'].strip():
                continue
                
            try:
                # Use the memory service directly to extract memories from conversation
                from app.services.memory_service import MemoryService
                
                memory_service = MemoryService()
                
                # Extract memories using LLM
                memories = await memory_service.extract_memories_with_llm(
                    text=conversation['transcription'],
                    source_id=conversation['id'],
                    source_type='conversation'
                )
                
                # Store each memory
                stored_count = 0
                for memory in memories:
                    try:
                        await memory_service.store_memory(memory)
                        stored_count += 1
                    except Exception as e:
                        logger.error(f"Failed to store memory: {e}")
                
                # Mark conversation as processed
                await db.execute("""
                    UPDATE conversations 
                    SET memory_extracted = 1,
                        memory_extracted_llm = 1,
                        memory_extracted_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (conversation['id'],))
                await db.commit()
                
                processed_conversations += 1
                logger.info(f"LLM extracted and stored {stored_count} memories from conversation {conversation['id']}")
                
                if processed_conversations % 3 == 0:
                    print(f"  Processed {processed_conversations}/{total_conversations} conversations...")
                    await asyncio.sleep(3)  # Delay to prevent database locks
                else:
                    await asyncio.sleep(0.5)  # Small delay between each conversation
                        
            except Exception as e:
                logger.error(f"Error processing conversation {conversation['id']}: {e}")
        
        print(f"✓ Processed {processed_conversations} conversations")
    
    # Step 5: Wait for async processing to complete
    print("\n⏳ Step 5: Waiting for async memory extraction to complete...")
    print("This may take several minutes as background tasks finish processing...")
    await asyncio.sleep(60)  # Give much more time for background processing
    
    # Step 6: Show final statistics
    print("\n📊 Step 6: Final statistics...")
    await show_statistics()
    
    print("\n" + "=" * 60)
    print("✅ MEMORY RECREATION COMPLETED!")
    print("All memories have been recreated using the main app pipeline.")
    print("=" * 60)


async def show_statistics():
    """Show memory extraction statistics"""
    
    # Get counts
    stats = await db.fetch_one("""
        SELECT 
            (SELECT COUNT(*) FROM agent_memories WHERE is_active = 1) as total_memories,
            (SELECT COUNT(*) FROM agent_memories WHERE score_source = 'llm_extraction' AND is_active = 1) as llm_memories,
            (SELECT COUNT(*) FROM agent_memories WHERE score_source = 'rule' AND is_active = 1) as rule_memories,
            (SELECT COUNT(*) FROM conversations WHERE memory_extracted_llm = 1) as processed_conversations,
            (SELECT COUNT(*) FROM conversations) as total_conversations,
            (SELECT COUNT(*) FROM entries WHERE memory_extracted_llm = 1) as processed_entries,
            (SELECT COUNT(*) FROM entries) as total_entries
    """)
    
    # Get detailed breakdown by score_source
    score_breakdown = await db.fetch_all("""
        SELECT score_source, COUNT(*) as count
        FROM agent_memories 
        WHERE is_active = 1
        GROUP BY score_source
        ORDER BY count DESC
    """)
    
    print("\n" + "=" * 60)
    print("MEMORY EXTRACTION STATISTICS")
    print("=" * 60)
    print(f"Total Active Memories: {stats['total_memories']}")
    print(f"  - LLM Extracted: {stats['llm_memories']}")
    print(f"  - Rule-based: {stats['rule_memories']}")
    
    # Show detailed breakdown
    print(f"\nDetailed breakdown by score_source:")
    for item in score_breakdown:
        source = item['score_source'] or 'NULL'
        count = item['count']
        print(f"  - {source}: {count}")
    
    print(f"\nConversations: {stats['processed_conversations']}/{stats['total_conversations']} processed with LLM")
    print(f"Entries: {stats['processed_entries']}/{stats['total_entries']} processed with LLM")
    print("=" * 60)


async def main():
    """Main function to run the reprocessing"""
    
    print("\n" + "=" * 60)
    print("LLM MEMORY EXTRACTION REPROCESSING")
    print("=" * 60)
    print("\nThis script will reprocess existing entries and conversations")
    print("using LLM extraction for higher quality memories.")
    print("\nOptions:")
    print("1. Process only conversations")
    print("2. Process only entries")
    print("3. Process both")
    print("4. Clean duplicate memories")
    print("5. Show statistics only")
    print("6. Reset processing flags (allows reprocessing previously processed items)")
    print("7. Delete all rule-based memories (PERMANENT)")
    print("8. 🚀 Clear ALL memories and recreate using main app pipeline (RECOMMENDED)")
    print("9. 🐌 Clear ALL memories and recreate in SMALL BATCHES (SAFER for large datasets)")
    print("0. Exit")
    
    choice = input("\nEnter your choice (0-9): ").strip()
    
    if choice == "0":
        print("Exiting...")
        return
    
    # Set correct database path
    db.db_path = str(Path(__file__).parent.parent / "echo.db")
    print(f"Using database: {db.db_path}")
    
    # Connect to database
    await db.connect()
    
    try:
        if choice == "1":
            limit = input("Enter max conversations to process (or press Enter for all): ").strip()
            limit = int(limit) if limit else None
            await reprocess_conversations(limit=limit)
            
        elif choice == "2":
            limit = input("Enter max entries to process (or press Enter for all): ").strip()
            limit = int(limit) if limit else None
            await reprocess_entries(limit=limit)
            
        elif choice == "3":
            conv_limit = input("Enter max conversations to process (or press Enter for all): ").strip()
            conv_limit = int(conv_limit) if conv_limit else None
            entry_limit = input("Enter max entries to process (or press Enter for all): ").strip()
            entry_limit = int(entry_limit) if entry_limit else None
            
            print("\nProcessing conversations...")
            await reprocess_conversations(limit=conv_limit)
            print("\nProcessing entries...")
            await reprocess_entries(limit=entry_limit)
            
        elif choice == "4":
            await clean_duplicate_memories()
            
        elif choice == "5":
            pass  # Just show statistics
            
        elif choice == "6":
            await reset_processing_flags()
            
        elif choice == "7":
            await delete_rule_based_memories()
            
        elif choice == "8":
            await clear_all_memories_and_recreate_with_main_pipeline()
            
        elif choice == "9":
            await clear_all_memories_and_recreate_with_main_pipeline()
            
        else:
            print("Invalid choice")
        
        # Always show statistics at the end
        await show_statistics()
        
    finally:
        await db.disconnect()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
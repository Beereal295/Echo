#!/usr/bin/env python3
"""
One-time script to backfill memories from existing entries and conversations.

This script processes:
1. Existing journal entries (enhanced_text) to extract memories
2. Existing conversations to extract memories and generate embeddings
3. Updates conversations with embeddings, summaries, and key topics

Run this after the memory system migration to ensure backward compatibility.
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.memory_service import MemoryService
from app.db.database import db
from sentence_transformers import SentenceTransformer

class MemoryBackfillService:
    def __init__(self):
        self.memory_service = MemoryService()
        self.embedding_model = None
        
    async def initialize_embedding_model(self):
        """Initialize the embedding model."""
        try:
            self.embedding_model = SentenceTransformer('BAAI/bge-small-en-v1.5')
            print("✓ Embedding model loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load embedding model: {e}")
            return False
        return True

    async def backfill_entry_memories(self):
        """Process existing entries for memory extraction."""
        print("\n🔄 Processing existing journal entries for memory extraction...")
        
        # Get all entries with enhanced_text
        rows = await db.fetch_all("""
            SELECT id, enhanced_text
            FROM entries 
            WHERE enhanced_text IS NOT NULL 
            AND enhanced_text != ''
            ORDER BY id
        """)
        
        if not rows:
            print("   No entries with enhanced_text found")
            return 0
        
        total_memories = 0
        processed_entries = 0
        
        for row in rows:
            entry_id = row['id']
            enhanced_text = row['enhanced_text']
            
            try:
                memory_count = self.memory_service.process_entry_for_memories(entry_id, enhanced_text)
                total_memories += memory_count
                processed_entries += 1
                
                if memory_count > 0:
                    print(f"   ✓ Entry {entry_id}: extracted {memory_count} memories")
                
            except Exception as e:
                print(f"   ❌ Entry {entry_id}: failed to extract memories - {e}")
        
        print(f"   📊 Processed {processed_entries} entries, extracted {total_memories} total memories")
        return total_memories

    async def backfill_conversation_data(self):
        """Process existing conversations for embeddings and memory extraction."""
        print("\n🔄 Processing existing conversations...")
        
        if not self.embedding_model:
            print("   ❌ Embedding model not available, skipping conversation processing")
            return 0, 0
        
        # Get all conversations without embeddings
        rows = await db.fetch_all("""
            SELECT id, transcription, timestamp
            FROM conversations 
            WHERE embedding IS NULL
            ORDER BY id
        """)
        
        if not rows:
            print("   No conversations without embeddings found")
            return 0, 0
        
        total_memories = 0
        processed_conversations = 0
        
        for row in rows:
            conv_id = row['id']
            transcription = row['transcription']
            
            if not transcription:
                continue
                
            try:
                # Generate embedding
                embedding_vector = self.embedding_model.encode(transcription)
                embedding_json = json.dumps(embedding_vector.tolist())
                
                # Generate summary (first 500 chars)
                summary = transcription[:500] if len(transcription) > 500 else transcription
                
                # Extract key topics
                key_topics = self._extract_key_topics(transcription)
                
                # Update conversation with metadata
                await db.execute("""
                    UPDATE conversations 
                    SET embedding = ?, summary = ?, key_topics = ?, updated_at = ?
                    WHERE id = ?
                """, (embedding_json, summary, json.dumps(key_topics), datetime.now().isoformat(), conv_id))
                
                # Commit after each conversation update to release locks
                await db.commit()
                
                # Extract memories from conversation (with retry logic)
                memory_count = 0
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        memory_count = self.memory_service.process_conversation_for_memories(conv_id, transcription)
                        break
                    except Exception as memory_error:
                        if "database is locked" in str(memory_error) and attempt < max_retries - 1:
                            print(f"   ⏳ Database locked, retrying in {attempt + 1}s...")
                            await asyncio.sleep(attempt + 1)  # Progressive backoff
                        else:
                            print(f"   ❌ Memory extraction failed: {memory_error}")
                            break
                
                total_memories += memory_count
                processed_conversations += 1
                
                print(f"   ✓ Conversation {conv_id}: added embedding + {memory_count} memories")
                
            except Exception as e:
                print(f"   ❌ Conversation {conv_id}: failed to process - {e}")
        
        # Final commit for any remaining changes
        try:
            await db.commit()
        except Exception as e:
            print(f"   ⚠️ Final commit warning: {e}")
        
        print(f"   📊 Processed {processed_conversations} conversations, extracted {total_memories} total memories")
        return processed_conversations, total_memories
    
    def _extract_key_topics(self, transcription: str) -> list:
        """Extract key topics from conversation transcription."""
        important_words = ['work', 'family', 'health', 'stress', 'happy', 'sad', 
                          'anxious', 'project', 'relationship', 'goal', 'problem',
                          'success', 'failure', 'love', 'fear', 'hope', 'dream']
        
        topics = []
        text_lower = transcription.lower()
        
        for word in important_words:
            if word in text_lower:
                topics.append(word)
        
        return topics[:5]  # Limit to top 5 topics

    async def verify_memory_extraction(self):
        """Verify that memories were extracted successfully."""
        print("\n📊 Verifying memory extraction...")
        
        # Get memory counts by type
        memory_stats = await db.fetch_all("""
            SELECT memory_type, COUNT(*) as count
            FROM agent_memories
            WHERE is_active = 1
            GROUP BY memory_type
        """)
        
        total_memories = 0
        for stat in memory_stats:
            print(f"   {stat['memory_type']}: {stat['count']} memories")
            total_memories += stat['count']
        
        print(f"   Total active memories: {total_memories}")
        
        # Get sample memories
        sample_memories = await db.fetch_all("""
            SELECT memory_type, content
            FROM agent_memories
            WHERE is_active = 1
            ORDER BY importance_score DESC
            LIMIT 5
        """)
        
        if sample_memories:
            print("\n   Sample high-importance memories:")
            for memory in sample_memories:
                content_preview = memory['content'][:80] + "..." if len(memory['content']) > 80 else memory['content']
                print(f"     [{memory['memory_type']}] {content_preview}")

async def main():
    """Run the memory backfill process."""
    print("🚀 Starting Memory System Backfill")
    print("=" * 50)
    
    # Initialize database
    await db.connect()
    
    try:
        service = MemoryBackfillService()
        
        # Initialize embedding model
        if not await service.initialize_embedding_model():
            print("❌ Cannot continue without embedding model")
            return
        
        # Process existing entries
        entry_memories = await service.backfill_entry_memories()
        
        # Process existing conversations
        conv_count, conv_memories = await service.backfill_conversation_data()
        
        # Verify results
        await service.verify_memory_extraction()
        
        print("\n" + "=" * 50)
        print("✅ Memory Backfill Complete!")
        print(f"   📝 Processed entries: {entry_memories} memories extracted")
        print(f"   💬 Processed conversations: {conv_count} conversations, {conv_memories} memories")
        print(f"   🧠 Total new memories: {entry_memories + conv_memories}")
        
    except Exception as e:
        print(f"\n❌ Backfill failed: {e}")
        raise
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
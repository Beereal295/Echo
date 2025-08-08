"""
Memory Service for Echo

Handles extraction, storage, and retrieval of agent memories.
Three types of memory:
1. Personal facts (name, occupation, pets, relationships)
2. Preferences (communication style, likes/dislikes)
3. Habits/Patterns (behavioral patterns, routines)
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer

from app.db.database import db

logger = logging.getLogger(__name__)

class MemoryService:
    def __init__(self):
        self.embedding_model = None
        self._init_embedding_model()
    
    def _init_embedding_model(self):
        """Initialize the BGE-small embedding model (same as used for entries)."""
        try:
            self.embedding_model = SentenceTransformer('BAAI/bge-small-en-v1.5')
            logger.info("Memory embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.embedding_model = None
    
    def extract_memories_from_conversation(self, conversation_text: str, conversation_id: int) -> List[Dict[str, Any]]:
        """
        Extract memories from a conversation using LLM.
        
        This would normally use an LLM to identify:
        - Personal facts: "My name is X", "I work at Y", "I have a cat named Z"
        - Preferences: "I prefer X", "I don't like Y", "Call me Z"
        - Habits: "I usually X", "Every morning I Y"
        
        For now, using simple pattern matching as placeholder.
        """
        memories = []
        
        # Simple pattern matching for MVP (replace with LLM extraction later)
        patterns = {
            'factual': [
                (r"my name is (\w+)", "name"),
                (r"i work at (\w+)", "workplace"),
                (r"i have a (\w+) named (\w+)", "pet"),
                (r"i live in (\w+)", "location"),
                (r"i'm (\d+) years old", "age"),
            ],
            'behavioral': [
                (r"i (always|usually|often) (\w+)", "habit"),
                (r"every (morning|evening|day) i (\w+)", "routine"),
            ],
            'relational': [
                (r"my (wife|husband|partner|mom|dad|sister|brother) (\w+)", "relationship"),
            ],
            'preference': [
                (r"i (prefer|like|love) (\w+)", "preference"),
                (r"call me (\w+)", "nickname"),
                (r"i don't like (\w+)", "dislike"),
            ]
        }
        
        # For MVP, just store the raw conversation chunks that might contain memories
        # In production, this would use LLM to extract structured memories
        
        # Extract potential memory sentences
        sentences = conversation_text.split('.')
        for sentence in sentences:
            sentence = sentence.strip().lower()
            if any(keyword in sentence for keyword in ['my', 'i ', "i'm", "i've", 'prefer', 'like', 'usually']):
                # This looks like it might contain personal information
                memory = {
                    'content': sentence,
                    'memory_type': self._classify_memory_type(sentence),
                    'key_entities': self._extract_entities(sentence),
                    'source_conversation_id': conversation_id,
                    'importance_score': self._calculate_importance(sentence)
                }
                memories.append(memory)
        
        return memories
    
    def _classify_memory_type(self, text: str) -> str:
        """Classify memory type based on content."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['name', 'work', 'live', 'years old', 'have a']):
            return 'factual'
        elif any(word in text_lower for word in ['prefer', 'like', 'love', 'hate', "don't like", 'call me']):
            return 'preference'
        elif any(word in text_lower for word in ['usually', 'always', 'often', 'every']):
            return 'behavioral'
        elif any(word in text_lower for word in ['wife', 'husband', 'partner', 'mom', 'dad', 'sister', 'brother', 'friend']):
            return 'relational'
        else:
            return 'contextual'
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract key entities from text for indexing."""
        # Simple keyword extraction for MVP
        important_words = []
        keywords = ['name', 'work', 'cat', 'dog', 'pet', 'wife', 'husband', 'partner', 
                   'mom', 'dad', 'sister', 'brother', 'friend', 'job', 'company']
        
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                important_words.append(keyword)
        
        return important_words
    
    def _calculate_importance(self, text: str) -> float:
        """Calculate importance score for a memory."""
        # Higher importance for personal facts and preferences
        if self._classify_memory_type(text) in ['factual', 'preference']:
            return 5.0
        elif self._classify_memory_type(text) == 'relational':
            return 4.0
        else:
            return 2.0
    
    async def store_memory(self, memory: Dict[str, Any]) -> int:
        """Store a memory in the database."""
        # Generate embedding if we have the model
        embedding = None
        if self.embedding_model and memory.get('content'):
            try:
                embedding_vector = self.embedding_model.encode(memory['content'])
                embedding = json.dumps(embedding_vector.tolist())
            except Exception as e:
                logger.error(f"Failed to generate embedding: {e}")
        
        # Check if similar memory already exists
        if embedding:
            # For now, just check exact duplicates
            existing = await db.fetch_one("""
                SELECT id FROM agent_memories 
                WHERE content = ? AND is_active = 1
            """, (memory['content'],))
            
            if existing:
                # Update access count and timestamp instead of creating duplicate
                await db.execute("""
                    UPDATE agent_memories 
                    SET access_count = access_count + 1,
                        last_accessed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (existing['id'],))
                await db.commit()
                return existing['id']
        
        # Insert new memory
        cursor = await db.execute("""
            INSERT INTO agent_memories (
                memory_type, content, key_entities, importance_score,
                embedding, source_conversation_id, related_entry_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            memory['memory_type'],
            memory['content'],
            json.dumps(memory.get('key_entities', [])),
            memory.get('importance_score', 1.0),
            embedding,
            memory.get('source_conversation_id'),
            memory.get('related_entry_id')
        ))
        
        await db.commit()
        return cursor.lastrowid
    
    async def retrieve_relevant_memories(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve memories relevant to a query.
        Uses semantic similarity if embeddings are available.
        """
        memories = []
        
        # If we have embedding model, use semantic search
        if self.embedding_model:
            try:
                query_embedding = self.embedding_model.encode(query)
                
                # Get all active memories with embeddings
                candidates = await db.fetch_all("""
                    SELECT id, memory_type, content, key_entities, importance_score,
                           embedding, created_at, last_accessed_at, access_count
                    FROM agent_memories
                    WHERE is_active = 1 AND embedding IS NOT NULL
                    ORDER BY importance_score DESC
                    LIMIT 100
                """)
                
                # Calculate similarities
                scored_memories = []
                for candidate in candidates:
                    if candidate['embedding']:
                        stored_embedding = np.array(json.loads(candidate['embedding']))
                        similarity = np.dot(query_embedding, stored_embedding) / (
                            np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding)
                        )
                        
                        # Combine similarity with importance score
                        final_score = (similarity * 0.7) + (candidate['importance_score'] / 10.0 * 0.3)
                        
                        scored_memories.append((final_score, dict(candidate)))
                
                # Sort by score and take top N
                scored_memories.sort(key=lambda x: x[0], reverse=True)
                memories = [m[1] for m in scored_memories[:limit]]
                
            except Exception as e:
                logger.error(f"Semantic search failed, falling back to keyword search: {e}")
        
        # Fallback to keyword search if semantic search fails or unavailable
        if not memories:
            # Simple keyword-based retrieval
            memories = await db.fetch_all("""
                SELECT id, memory_type, content, key_entities, importance_score,
                       created_at, last_accessed_at, access_count
                FROM agent_memories
                WHERE is_active = 1
                ORDER BY importance_score DESC, access_count DESC
                LIMIT ?
            """, (limit,))
        
        # Update access timestamps
        if memories:
            memory_ids = [m['id'] for m in memories]
            placeholders = ','.join('?' * len(memory_ids))
            await db.execute(f"""
                UPDATE agent_memories
                SET last_accessed_at = CURRENT_TIMESTAMP,
                    access_count = access_count + 1
                WHERE id IN ({placeholders})
            """, tuple(memory_ids))
            await db.commit()
        
        return memories
    
    async def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of stored memories."""
        # Get counts by type
        type_counts_result = await db.fetch_all("""
            SELECT memory_type, COUNT(*) as count
            FROM agent_memories
            WHERE is_active = 1
            GROUP BY memory_type
        """)
        
        type_counts = {row['memory_type']: row['count'] for row in type_counts_result}
        
        # Get total count
        total_result = await db.fetch_one("""
            SELECT COUNT(*) as total
            FROM agent_memories
            WHERE is_active = 1
        """)
        
        total = total_result['total'] if total_result else 0
        
        # Get most accessed memories
        most_accessed = await db.fetch_all("""
            SELECT content, access_count
            FROM agent_memories
            WHERE is_active = 1
            ORDER BY access_count DESC
            LIMIT 5
        """)
        
        return {
            'total_memories': total,
            'by_type': type_counts,
            'most_accessed': most_accessed
        }
    
    async def deactivate_outdated_memories(self, memory_id: int):
        """Deactivate a memory (soft delete)."""
        await db.execute("""
            UPDATE agent_memories
            SET is_active = 0
            WHERE id = ?
        """, (memory_id,))
        await db.commit()
    
    async def process_conversation_for_memories(self, conversation_id: int, conversation_text: str) -> int:
        """
        Process a conversation and extract/store memories.
        Returns the number of memories extracted.
        """
        # Extract memories
        memories = self.extract_memories_from_conversation(conversation_text, conversation_id)
        
        # Store each memory
        stored_count = 0
        for memory in memories:
            try:
                await self.store_memory(memory)
                stored_count += 1
            except Exception as e:
                logger.error(f"Failed to store memory: {e}")
        
        logger.info(f"Extracted and stored {stored_count} memories from conversation {conversation_id}")
        return stored_count
    
    async def process_entry_for_memories(self, entry_id: int, enhanced_text: str) -> int:
        """
        Process a journal entry and extract/store memories.
        Uses enhanced text for better quality extraction.
        Returns the number of memories extracted.
        """
        if not enhanced_text:
            return 0
            
        # Extract memories from enhanced entry text
        memories = []
        
        # Similar extraction logic but adapted for journal entries
        sentences = enhanced_text.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in ['my', 'i ', "i'm", "i've", 'prefer', 'like', 'usually', 'always', 'every']):
                memory = {
                    'content': sentence,
                    'memory_type': self._classify_memory_type(sentence),
                    'key_entities': self._extract_entities(sentence),
                    'related_entry_id': entry_id,  # Link to entry instead of conversation
                    'source_conversation_id': None,
                    'importance_score': self._calculate_importance(sentence) * 1.5  # Entries are more important than conversations
                }
                memories.append(memory)
        
        # Store each memory
        stored_count = 0
        for memory in memories:
            try:
                await self.store_memory(memory)
                stored_count += 1
            except Exception as e:
                logger.error(f"Failed to store memory from entry: {e}")
        
        logger.info(f"Extracted and stored {stored_count} memories from entry {entry_id}")
        return stored_count
    
    def format_memories_for_context(self, memories: List[Dict[str, Any]]) -> str:
        """
        Format memories into a string for LLM context injection.
        Groups by type for better organization.
        """
        if not memories:
            return ""
        
        # Group memories by type
        grouped = {
            'factual': [],
            'preference': [],
            'behavioral': [],
            'relational': [],
            'contextual': []
        }
        
        for memory in memories:
            memory_type = memory.get('memory_type', 'contextual')
            grouped[memory_type].append(memory['content'])
        
        # Format into readable context
        context_parts = []
        
        if grouped['factual']:
            context_parts.append("Personal Facts:\n" + "\n".join(f"- {m}" for m in grouped['factual']))
        
        if grouped['preference']:
            context_parts.append("Preferences:\n" + "\n".join(f"- {m}" for m in grouped['preference']))
        
        if grouped['behavioral']:
            context_parts.append("Habits & Patterns:\n" + "\n".join(f"- {m}" for m in grouped['behavioral']))
        
        if grouped['relational']:
            context_parts.append("Relationships:\n" + "\n".join(f"- {m}" for m in grouped['relational']))
        
        if grouped['contextual']:
            context_parts.append("Context:\n" + "\n".join(f"- {m}" for m in grouped['contextual']))
        
        return "\n\n".join(context_parts)
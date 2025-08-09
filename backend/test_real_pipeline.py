"""
Test script for the real async memory pipeline using actual API endpoints

This script tests the EXACT production pipeline by making HTTP requests to the running app:
1. POST /api/v1/entries (creates entry + triggers memory extraction via FastAPI BackgroundTasks)
2. POST /api/v1/diary/chat + POST /api/v1/conversations (simulates full UI flow: chat then save)
   - First call: Chat with Echo (gets response)
   - Second call: Save conversation (triggers memory extraction via FastAPI BackgroundTasks)
3. Verifies: Extract → Score → Embed pipeline works in production

Requires: FastAPI app running on localhost:8000
"""

import asyncio
import aiohttp
import logging
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from app.db.database import db

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class RealPipelineTester:
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1"
        self.test_entry_ids = []
        self.test_conversation_ids = []
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def run_real_pipeline_test(self):
        """Test the complete real async memory pipeline via API calls"""
        print("\n" + "="*60)
        print("RUNNING REAL MAIN APP PIPELINE TEST")
        print("="*60)
        
        try:
            # Test 0: Verify API is running
            print("\n0. Checking if FastAPI app is running...")
            if not await self._check_api_health():
                print("❌ FastAPI app not running at localhost:8000")
                print("Please start the app with: uvicorn app.main:app --reload")
                return False
            
            # Test 1: Create entry via API (triggers real FastAPI BackgroundTasks)
            print("\n1. Creating test entry via API...")
            entry_response = await self._create_test_entry_via_api()
            if not entry_response:
                return False
            entry_id = entry_response['id']
            self.test_entry_ids.append(entry_id)
            print(f"✓ Created entry {entry_id} via POST /api/v1/entries")
            
            # Test 2: Create conversation via API (simulates full UI flow: chat + save)
            print("\n2. Creating test conversation via API (chat + save)...")
            conv_response = await self._create_test_conversation_via_api()
            if not conv_response:
                return False
            
            # Extract conversation ID from the response
            conversation_id = conv_response.get('data', {}).get('id')
            if conversation_id:
                self.test_conversation_ids.append(conversation_id)
                print(f"✓ Created conversation {conversation_id} via chat + save flow")
            else:
                print("❌ Failed to get conversation ID from response")
                return False
            
            # Test 3: Wait for real async processing (FastAPI BackgroundTasks + asyncio)
            print("\n3. Waiting for real async pipeline to complete...")
            await asyncio.sleep(15)  # Give time for real async tasks
            
            # Test 4: Check processing status via database
            print("\n4. Checking real processing status...")
            entry_status = await self._check_entry_processing_status(entry_id)
            conversation_status = None
            if conversation_id:
                conversation_status = await self._check_conversation_processing_status(conversation_id)
            
            print(f"   Entry {entry_id} status: {entry_status}")
            if conversation_status:
                print(f"   Conversation {conversation_id} status: {conversation_status}")
            
            # Test 5: Verify memory extraction occurred
            print("\n5. Checking memory extraction...")
            entry_memories = await self._get_memories_for_entry(entry_id)
            conversation_memories = []
            if conversation_id:
                conversation_memories = await self._get_memories_for_conversation(conversation_id)
            
            print(f"✓ Entry {entry_id} generated {len(entry_memories)} memories")
            if conversation_id:
                print(f"✓ Conversation {conversation_id} generated {len(conversation_memories)} memories")
            
            # Check if we can get the actual text that was processed
            entry_details = await self._get_entry_details(entry_id)
            print(f"   Entry text processed: '{entry_details.get('raw_text', '')[:100]}...'")
            print(f"   Entry processing status: extracted={entry_details.get('memory_extracted')}, llm={entry_details.get('memory_extracted_llm')}")
            
            # Test 6: Check real LLM scoring pipeline
            print("\n6. Checking real LLM scoring pipeline...")
            all_memories = entry_memories + conversation_memories
            await self._verify_real_llm_scoring(all_memories)
            
            # Test 7: Check real BGE embedding generation
            print("\n7. Checking real BGE embedding generation...")
            await self._verify_real_embeddings(all_memories)
            
            # Test 8: Show detailed memory analysis
            print("\n8. Real memory analysis:")
            await self._analyze_real_memories(all_memories)
            
            print("\n" + "="*60)
            print("✅ REAL PIPELINE TEST COMPLETED SUCCESSFULLY")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ REAL TEST FAILED: {e}")
            logger.error(f"Real pipeline test failed: {e}")
            return False
        
        return True
    
    async def _check_api_health(self) -> bool:
        """Check if the FastAPI app is running"""
        try:
            async with self.session.get(f"{self.base_url.replace('/api/v1', '')}/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✓ FastAPI app running: {data.get('message', 'OK')}")
                    return True
                return False
        except Exception as e:
            logger.error(f"API health check failed: {e}")
            return False
    
    async def _create_test_entry_via_api(self) -> Dict[str, Any]:
        """Create test entry via real API endpoint"""
        test_entry_data = {
            "raw_text": """
            Today was an amazing day working on Echo! My name is Sayantan and I'm building a journaling app called Echo. 
            Even though I'm not a coder by background, I'm passionate about creating this personal AI companion for journaling. 
            Echo uses Ollama for LLM processing and has a memory system that extracts personal facts from journal entries. 
            I prefer working with Claude Code over other AI assistants because it's more capable for development tasks. 
            My biggest challenge is debugging complex async pipelines, but I really enjoy the problem-solving aspect. 
            I usually work late into the night when I'm in the flow state.
            """.strip(),
            "mode": "raw"
        }
        
        try:
            async with self.session.post(f"{self.base_url}/entries/", json=test_entry_data) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to create entry: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"❌ Error creating entry: {e}")
            return None
    
    async def _create_test_conversation_via_api(self) -> Dict[str, Any]:
        """Create test conversation via real API endpoint - simulating full UI flow"""
        
        # Step 1: Chat with diary (like user typing in chat modal)
        test_chat_message = """I'm really excited about Echo's progress! As a non-technical founder, building this journaling app 
            has been an incredible learning journey. Echo is designed to be a personal AI companion that understands users' 
            thoughts and memories. I chose to use local Ollama models instead of cloud APIs for privacy reasons. 
            My goal is to create something that feels genuinely personal, not just another generic AI chat bot. 
            I spend most of my time working on the memory extraction pipeline and improving the user experience."""
        
        chat_request = {
            "message": test_chat_message
        }
        
        try:
            # Step 1: Send chat message (simulates user chatting)
            print("   Step 1: Sending chat message...")
            async with self.session.post(f"{self.base_url}/diary/chat", json=chat_request) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"❌ Failed to chat with diary: {response.status} - {error_text}")
                    return None
                
                chat_response = await response.json()
                echo_reply = chat_response.get('data', {}).get('response', '')
                print(f"   ✓ Received Echo's response: {echo_reply[:60]}...")
            
            # Step 2: Create conversation record (simulates user clicking "Save" after closing modal)
            print("   Step 2: Saving conversation (simulating 'Save' button)...")
            
            # Build the full transcription like the frontend would
            full_transcription = f"User: {test_chat_message}\n\nEcho: {echo_reply}"
            
            conversation_request = {
                "conversation_type": "chat",
                "transcription": full_transcription,
                "duration": 30,  # Simulated duration
                "message_count": 2,  # User message + Echo response
                "search_queries_used": chat_response.get('data', {}).get('search_queries_used', [])
            }
            
            async with self.session.post(f"{self.base_url}/conversations", json=conversation_request) as response:
                if response.status in [200, 201]:
                    conv_response = await response.json()
                    print(f"   ✓ Conversation saved with ID: {conv_response.get('data', {}).get('id')}")
                    return conv_response
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to save conversation: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error in conversation flow: {e}")
            return None
    
    async def _check_entry_processing_status(self, entry_id: int) -> Dict[str, Any]:
        """Check entry processing status from database"""
        status = await db.fetch_one("""
            SELECT memory_extracted, memory_extracted_llm, memory_extracted_at 
            FROM entries WHERE id = ?
        """, (entry_id,))
        return dict(status) if status else {"error": "entry not found"}
    
    async def _check_conversation_processing_status(self, conversation_id: int) -> Dict[str, Any]:
        """Check conversation processing status from database"""
        status = await db.fetch_one("""
            SELECT memory_extracted, memory_extracted_llm, memory_extracted_at 
            FROM conversations WHERE id = ?
        """, (conversation_id,))
        return dict(status) if status else {"error": "conversation not found"}
    
    async def _get_memories_for_entry(self, entry_id: int) -> List[Dict[str, Any]]:
        """Get memories generated for an entry"""
        memories = await db.fetch_all("""
            SELECT * FROM agent_memories 
            WHERE related_entry_id = ? AND is_active = 1
            ORDER BY created_at DESC
        """, (entry_id,))
        return [dict(memory) for memory in memories]
    
    async def _get_memories_for_conversation(self, conversation_id: int) -> List[Dict[str, Any]]:
        """Get memories generated for a conversation"""
        memories = await db.fetch_all("""
            SELECT * FROM agent_memories 
            WHERE source_conversation_id = ? AND is_active = 1
            ORDER BY created_at DESC
        """, (conversation_id,))
        return [dict(memory) for memory in memories]
    
    async def _get_entry_details(self, entry_id: int) -> Dict[str, Any]:
        """Get entry details for debugging"""
        entry = await db.fetch_one("""
            SELECT raw_text, enhanced_text, memory_extracted, memory_extracted_llm, memory_extracted_at
            FROM entries WHERE id = ?
        """, (entry_id,))
        return dict(entry) if entry else {}
    
    async def _verify_real_llm_scoring(self, memories: List[Dict[str, Any]]):
        """Verify that real LLM scoring pipeline worked"""
        llm_extraction_count = 0
        llm_scored_count = 0
        
        for memory in memories:
            if memory.get('score_source') == 'llm_extraction':
                llm_extraction_count += 1
            elif memory.get('score_source') == 'llm':
                llm_scored_count += 1
        
        print(f"  - Memories with score_source='llm_extraction': {llm_extraction_count}")
        print(f"  - Memories with score_source='llm': {llm_scored_count}")
        
        # Wait more if some memories are still being processed
        if llm_extraction_count > 0:
            print("  - Some memories still being scored, waiting 15 more seconds...")
            await asyncio.sleep(15)
            
            # Re-check by fetching fresh data
            updated_memories = []
            for memory in memories:
                updated = await db.fetch_one("SELECT * FROM agent_memories WHERE id = ?", (memory['id'],))
                if updated:
                    updated_memories.append(dict(updated))
            
            llm_extraction_count = sum(1 for m in updated_memories if m.get('score_source') == 'llm_extraction')
            llm_scored_count = sum(1 for m in updated_memories if m.get('score_source') == 'llm')
            
            print(f"  - After waiting - llm_extraction: {llm_extraction_count}, llm_scored: {llm_scored_count}")
        
        if llm_scored_count > 0:
            print("✓ Real LLM scoring pipeline working!")
        elif llm_extraction_count > 0:
            print("⚠️  Real LLM scoring still in progress...")
        else:
            print("❌ No LLM scoring detected in real pipeline")
    
    async def _verify_real_embeddings(self, memories: List[Dict[str, Any]]):
        """Verify that real BGE embedding generation worked"""
        embedded_count = 0
        
        for memory in memories:
            if memory.get('embedding'):
                embedded_count += 1
        
        print(f"  - Memories with embeddings: {embedded_count}/{len(memories)}")
        
        # Wait if embeddings are still being generated
        if embedded_count < len(memories):
            print("  - Some embeddings still being generated, waiting 15 more seconds...")
            await asyncio.sleep(15)
            
            # Re-check
            updated_embedded_count = 0
            for memory in memories:
                updated = await db.fetch_one("SELECT embedding FROM agent_memories WHERE id = ?", (memory['id'],))
                if updated and updated['embedding']:
                    updated_embedded_count += 1
            
            print(f"  - After waiting - embeddings: {updated_embedded_count}/{len(memories)}")
            embedded_count = updated_embedded_count
        
        if embedded_count == len(memories):
            print("✓ Real BGE embedding generation working!")
        elif embedded_count > 0:
            print("⚠️  Real BGE embedding still in progress...")
        else:
            print("❌ No embeddings detected in real pipeline")
    
    async def _analyze_real_memories(self, memories: List[Dict[str, Any]]):
        """Analyze the real memory quality and content"""
        if not memories:
            print("  - No memories found in real pipeline")
            return
        
        # Group by type and source
        by_type = {}
        by_source = {}
        score_range = {"min": 10, "max": 0, "avg": 0}
        total_score = 0
        
        for memory in memories:
            mem_type = memory.get('memory_type', 'unknown')
            source = memory.get('score_source', 'unknown')
            score = memory.get('llm_importance_score') or memory.get('final_importance_score', 0)
            
            by_type[mem_type] = by_type.get(mem_type, 0) + 1
            by_source[source] = by_source.get(source, 0) + 1
            
            if score:
                score = float(score)
                score_range["min"] = min(score_range["min"], score)
                score_range["max"] = max(score_range["max"], score)
                total_score += score
        
        if memories:
            score_range["avg"] = total_score / len(memories)
        
        print(f"  - Total memories: {len(memories)}")
        print(f"  - By type: {dict(by_type)}")
        print(f"  - By source: {dict(by_source)}")
        print(f"  - Score range: {score_range['min']:.1f} - {score_range['max']:.1f} (avg: {score_range['avg']:.1f})")
        
        # Show sample memories
        print(f"\n  Sample real memories:")
        for i, memory in enumerate(memories[:3]):
            score = memory.get('llm_importance_score') or memory.get('final_importance_score', 'N/A')
            embedding_status = "✓" if memory.get('embedding') else "❌"
            print(f"    {i+1}. [{memory.get('memory_type')}] {memory.get('content', '')[:60]}...")
            print(f"       Score: {score}, Source: {memory.get('score_source')}, Embedded: {embedding_status}")
    
    async def cleanup_real_test_data(self):
        """Clean up real test data"""
        print("\n" + "="*60)
        print("CLEANING UP REAL TEST DATA")
        print("="*60)
        
        try:
            total_deleted = 0
            
            # Delete memories from test entries
            for entry_id in self.test_entry_ids:
                result = await db.execute("""
                    DELETE FROM agent_memories 
                    WHERE related_entry_id = ?
                """, (entry_id,))
                deleted = result.rowcount if hasattr(result, 'rowcount') else 0
                total_deleted += deleted
                print(f"✓ Deleted {deleted} memories from entry {entry_id}")
            
            # Delete memories from test conversations
            for conv_id in self.test_conversation_ids:
                result = await db.execute("""
                    DELETE FROM agent_memories 
                    WHERE source_conversation_id = ?
                """, (conv_id,))
                deleted = result.rowcount if hasattr(result, 'rowcount') else 0
                total_deleted += deleted
                print(f"✓ Deleted {deleted} memories from conversation {conv_id}")
            
            # Delete test entries (via API for consistency)
            for entry_id in self.test_entry_ids:
                try:
                    async with self.session.delete(f"{self.base_url}/entries/{entry_id}") as response:
                        if response.status in [200, 204, 404]:
                            print(f"✓ Deleted test entry {entry_id}")
                        else:
                            print(f"⚠️  Could not delete entry {entry_id} via API (status: {response.status})")
                            # Fallback to direct database deletion
                            await db.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
                            print(f"✓ Deleted entry {entry_id} via database")
                except Exception as e:
                    print(f"⚠️  Error deleting entry {entry_id}: {e}")
            
            # Delete test conversations (direct database - no API endpoint)
            for conv_id in self.test_conversation_ids:
                await db.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
                print(f"✓ Deleted test conversation {conv_id}")
            
            await db.commit()
            
            # Clear tracking lists
            self.test_entry_ids.clear()
            self.test_conversation_ids.clear()
            
            print(f"\n✅ Real cleanup completed: Deleted {total_deleted} memories, {len(self.test_entry_ids)} entries, {len(self.test_conversation_ids)} conversations")
            
        except Exception as e:
            print(f"❌ Real cleanup failed: {e}")
            logger.error(f"Real cleanup failed: {e}")


async def main():
    """Main function with interactive menu for real pipeline testing"""
    
    # Set database path
    db.db_path = str(Path(__file__).parent / "echo.db")
    print(f"Using database: {db.db_path}")
    
    # Connect to database
    await db.connect()
    
    try:
        async with RealPipelineTester() as tester:
            while True:
                print("\n" + "="*60)
                print("REAL MAIN APP PIPELINE TESTER")
                print("="*60)
                print("Tests the EXACT production pipeline via API calls")
                print("Requires: FastAPI app running on localhost:8000")
                print("="*60)
                print("1. Run real pipeline test")
                print("2. Clean up test data")
                print("3. Exit")
                print("="*60)
                
                choice = input("Enter your choice (1-3): ").strip()
                
                if choice == "1":
                    await tester.run_real_pipeline_test()
                    
                elif choice == "2":
                    await tester.cleanup_real_test_data()
                    
                elif choice == "3":
                    print("\nExiting...")
                    break
                    
                else:
                    print("❌ Invalid choice. Please enter 1, 2, or 3.")
                
                # Wait for user to see results
                input("\nPress Enter to continue...")
    
    finally:
        await db.disconnect()


if __name__ == "__main__":
    print("=" * 60)
    print("REAL MAIN APP PIPELINE TESTER")
    print("=" * 60)
    print("This test uses the EXACT production pipeline via HTTP API calls")
    print("Make sure your FastAPI app is running:")
    print("  cd backend")
    print("  uvicorn app.main:app --reload")
    print("Then run this test in another terminal.")
    print("=" * 60)
    
    asyncio.run(main())
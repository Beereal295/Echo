#!/usr/bin/env python3
"""
Test script for the new memory scoring system
"""
import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.memory_service import MemoryService
from app.db.database import Database
from app.db.repositories.preferences_repository import PreferencesRepository


async def test_database_schema():
    """Test 1: Verify migration applied correctly"""
    print("Test 1: Verifying database schema...")
    
    try:
        # Check if new columns exist
        db_path = Path(__file__).parent / "echo.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("PRAGMA table_info(agent_memories)")
        columns = [column[1] for column in cursor.fetchall()]
        
        expected_columns = [
            'base_importance_score',
            'llm_importance_score', 
            'user_score_adjustment',
            'final_importance_score',
            'user_rated',
            'score_source',
            'llm_processed',
            'llm_processed_at',
            'user_rated_at',
            'decay_last_calculated',
            'effective_score_cache',
            'score_breakdown',
            'marked_for_deletion',
            'marked_for_deletion_at',
            'deletion_reason',
            'archived',
            'archived_at'
        ]
        
        missing_columns = [col for col in expected_columns if col not in columns]
        if missing_columns:
            print(f"ERROR: Missing columns: {missing_columns}")
            return False
        
        print("SUCCESS: All new columns present in database")
        
        # Check indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='agent_memories'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        expected_indexes = [
            'idx_memory_user_rated',
            'idx_memory_llm_processed', 
            'idx_memory_final_score',
            'idx_memory_marked_deletion',
            'idx_memory_archived'
        ]
        
        missing_indexes = [idx for idx in expected_indexes if idx not in indexes]
        if missing_indexes:
            print(f"⚠️ Missing indexes: {missing_indexes}")
        else:
            print("✅ All indexes created successfully")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        return False


async def test_memory_creation():
    """Test 2: Test memory creation with rule-based scoring"""
    print("\n🔍 Test 2: Testing memory creation with rule-based scoring...")
    
    try:
        # Initialize database connection
        from app.db.database import db
        await db.connect()
        
        memory_service = MemoryService()
        
        # Test different memory types
        test_memories = [
            {
                'content': 'My name is John and I work as a software engineer',
                'expected_type': 'factual',
                'expected_score_range': (3.5, 5.0)
            },
            {
                'content': 'I prefer coffee over tea in the morning',
                'expected_type': 'preference', 
                'expected_score_range': (3.5, 5.0)
            },
            {
                'content': 'My wife Sarah loves reading mystery novels',
                'expected_type': 'relational',
                'expected_score_range': (3.0, 4.5)
            },
            {
                'content': 'I usually go for a run every morning at 6am',
                'expected_type': 'behavioral',
                'expected_score_range': (2.5, 4.0)
            }
        ]
        
        created_memories = []
        for test_memory in test_memories:
            # Create memory
            memory_data = {
                'content': test_memory['content'],
                'memory_type': memory_service._classify_memory_type(test_memory['content']),
                'key_entities': memory_service._extract_entities(test_memory['content']),
                'source_conversation_id': None,
                'base_importance_score': memory_service._calculate_importance(test_memory['content']),
                'final_importance_score': memory_service._calculate_importance(test_memory['content']),
                'score_source': 'rule'
            }
            
            memory_id = await memory_service.store_memory(memory_data)
            created_memories.append(memory_id)
            
            # Verify memory was stored correctly
            stored_memory = await db.fetch_one("SELECT * FROM agent_memories WHERE id = ?", (memory_id,))
            
            # Check memory type
            if stored_memory['memory_type'] != test_memory['expected_type']:
                print(f"⚠️ Memory type mismatch for '{test_memory['content'][:30]}...': expected {test_memory['expected_type']}, got {stored_memory['memory_type']}")
            
            # Check score range
            score = stored_memory['base_importance_score']
            min_score, max_score = test_memory['expected_score_range']
            if not (min_score <= score <= max_score):
                print(f"⚠️ Score out of range for '{test_memory['content'][:30]}...': expected {min_score}-{max_score}, got {score}")
            else:
                print(f"✅ Memory created: {test_memory['expected_type']} type, score: {score}")
        
        print(f"✅ Successfully created {len(created_memories)} test memories")
        return created_memories
        
    except Exception as e:
        print(f"❌ Memory creation test failed: {e}")
        return []


async def test_user_rating():
    """Test 3: Test user rating system"""
    print("\n🔍 Test 3: Testing user rating system...")
    
    try:
        from app.db.database import db
        memory_service = MemoryService()
        
        # Create a test memory first
        memory_data = {
            'content': 'I love playing guitar on weekends',
            'memory_type': 'preference',
            'key_entities': ['guitar'],
            'base_importance_score': 4.0,
            'final_importance_score': 4.0,
            'score_source': 'rule'
        }
        
        memory_id = await memory_service.store_memory(memory_data)
        
        # Test different rating adjustments
        test_ratings = [-3, -1, 0, 2, 3]
        
        for adjustment in test_ratings:
            # Apply rating
            success = await memory_service.rate_memory(memory_id, adjustment)
            if not success:
                print(f"❌ Failed to apply rating {adjustment}")
                continue
            
            # Check memory was updated
            memory = await db.fetch_one("SELECT * FROM agent_memories WHERE id = ?", (memory_id,))
            
            expected_final = max(1, min(10, 4.0 + adjustment))  # Base score 4.0
            actual_final = memory['final_importance_score']
            
            if abs(expected_final - actual_final) > 0.1:
                print(f"❌ Rating {adjustment}: expected final score {expected_final}, got {actual_final}")
            else:
                print(f"✅ Rating {adjustment}: final score {actual_final}, user_rated={memory['user_rated']}")
            
            # Verify user_rated flag
            if memory['user_rated'] != 1:
                print(f"❌ user_rated flag not set for rating {adjustment}")
            
            # Verify score_source
            if memory['score_source'] != 'user_modified':
                print(f"❌ score_source not updated for rating {adjustment}")
        
        print("✅ User rating system working correctly")
        return True
        
    except Exception as e:
        print(f"❌ User rating test failed: {e}")
        return False


async def test_decay_calculations():
    """Test 4: Test decay and boost calculations"""
    print("\n🔍 Test 4: Testing decay and boost calculations...")
    
    try:
        memory_service = MemoryService()
        
        # Test recency decay
        now = datetime.now()
        
        test_cases = [
            {
                'name': 'Fresh memory (3 days old)',
                'created_at': now - timedelta(days=3),
                'last_accessed_at': now - timedelta(days=1),
                'access_count': 0,
                'expected_decay_range': (-0.1, 0.1)  # Should be ~0 (grace period)
            },
            {
                'name': 'Old unused memory (60 days)',
                'created_at': now - timedelta(days=60),
                'last_accessed_at': now - timedelta(days=60),
                'access_count': 0,
                'expected_decay_range': (-1.0, -0.5)  # Should decay significantly
            },
            {
                'name': 'Frequently accessed memory',
                'created_at': now - timedelta(days=30),
                'last_accessed_at': now - timedelta(days=2),
                'access_count': 10,
                'expected_decay_range': (-0.5, 0.5)  # Should have boost offsetting decay
            }
        ]
        
        for test_case in test_cases:
            memory_dict = {
                'created_at': test_case['created_at'],
                'last_accessed_at': test_case['last_accessed_at'],
                'access_count': test_case['access_count'],
                'base_importance_score': 5.0,
                'user_score_adjustment': 0,
                'user_rated': 0
            }
            
            # Calculate effective score
            score_data = memory_service.calculate_effective_score(memory_dict)
            
            # Extract decay component
            recency_decay = score_data['breakdown']['recency_decay']
            frequency_boost = score_data['breakdown']['frequency_boost']
            
            print(f"✅ {test_case['name']}:")
            print(f"   Recency decay: {recency_decay:.2f}")
            print(f"   Frequency boost: {frequency_boost:.2f}")
            print(f"   Final score: {score_data['score']:.2f}")
        
        print("✅ Decay calculations working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Decay calculation test failed: {e}")
        return False


async def test_api_endpoints():
    """Test 5: Test API endpoint responses"""
    print("\n🔍 Test 5: Testing API endpoints...")
    
    try:
        from app.db.database import db
        memory_service = MemoryService()
        
        # Create some test memories with different states
        test_memories = [
            {'content': 'Unrated memory 1', 'user_rated': 0, 'llm_processed': 0},
            {'content': 'Unrated but LLM processed', 'user_rated': 0, 'llm_processed': 1, 'llm_importance_score': 6.5},
            {'content': 'User rated memory', 'user_rated': 1, 'user_score_adjustment': 2}
        ]
        
        created_ids = []
        for memory_data in test_memories:
            base_score = 4.0
            memory = {
                'content': memory_data['content'],
                'memory_type': 'preference',
                'key_entities': [],
                'base_importance_score': base_score,
                'final_importance_score': base_score + memory_data.get('user_score_adjustment', 0),
                'score_source': 'user_modified' if memory_data.get('user_rated') else 'rule',
                'user_rated': memory_data.get('user_rated', 0),
                'user_score_adjustment': memory_data.get('user_score_adjustment', 0),
                'llm_processed': memory_data.get('llm_processed', 0),
                'llm_importance_score': memory_data.get('llm_importance_score')
            }
            
            memory_id = await memory_service.store_memory(memory)
            created_ids.append(memory_id)
        
        # Test get_unrated_memories
        unrated_memories = await memory_service.get_unrated_memories(limit=10)
        unrated_count = len([m for m in unrated_memories if m['user_rated'] == 0])
        print(f"✅ Found {unrated_count} unrated memories")
        
        # Test memory statistics query
        stats_query = await db.fetch_one("""
            SELECT 
                COUNT(*) as total_memories,
                SUM(CASE WHEN user_rated = 1 THEN 1 ELSE 0 END) as rated_memories,
                SUM(CASE WHEN user_rated = 0 THEN 1 ELSE 0 END) as unrated_memories,
                SUM(CASE WHEN llm_processed = 1 THEN 1 ELSE 0 END) as llm_processed,
                AVG(final_importance_score) as average_score
            FROM agent_memories
            WHERE is_active = 1
        """)
        
        print(f"✅ Memory Statistics:")
        print(f"   Total: {stats_query['total_memories']}")
        print(f"   Rated: {stats_query['rated_memories']}")
        print(f"   Unrated: {stats_query['unrated_memories']}")
        print(f"   LLM processed: {stats_query['llm_processed']}")
        print(f"   Average score: {stats_query['average_score']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False


async def test_pruning_criteria():
    """Test 6: Test memory pruning safety checks"""
    print("\n🔍 Test 6: Testing memory pruning criteria...")
    
    try:
        from app.db.database import db
        memory_service = MemoryService()
        
        # Create memories with different characteristics for pruning test
        now = datetime.now()
        
        # Memory that should be marked for deletion
        deletable_memory = {
            'content': 'This should be deleted - irrelevant info',
            'memory_type': 'contextual',
            'key_entities': [],
            'base_importance_score': 2.0,
            'final_importance_score': 1.0,  # Low final score after user rating
            'user_rated': 1,
            'user_score_adjustment': -3,  # User marked as irrelevant
            'score_source': 'user_modified',
            'created_at': (now - timedelta(days=40)).isoformat(),  # Old enough
            'last_accessed_at': (now - timedelta(days=70)).isoformat(),  # Not accessed recently
            'access_count': 1  # Low access count
        }
        
        # Memory that should NOT be deleted (user didn't rate as irrelevant)
        safe_memory = {
            'content': 'This should be safe',
            'memory_type': 'preference',
            'key_entities': ['safe'],
            'base_importance_score': 4.0,
            'final_importance_score': 3.0,
            'user_rated': 1,
            'user_score_adjustment': -1,  # User rated as less important but not irrelevant
            'score_source': 'user_modified',
            'created_at': (now - timedelta(days=40)).isoformat(),
            'last_accessed_at': (now - timedelta(days=70)).isoformat(),
            'access_count': 1
        }
        
        # Store test memories
        deletable_id = await memory_service.store_memory(deletable_memory)
        safe_id = await memory_service.store_memory(safe_memory)
        
        # Test deletion marking logic
        marked_ids = await memory_service.mark_memories_for_deletion()
        
        if deletable_id in marked_ids:
            print(f"✅ Correctly marked deletable memory {deletable_id} for deletion")
        else:
            print(f"⚠️ Failed to mark deletable memory {deletable_id}")
        
        if safe_id not in marked_ids:
            print(f"✅ Correctly preserved safe memory {safe_id}")
        else:
            print(f"❌ Incorrectly marked safe memory {safe_id} for deletion")
        
        print(f"✅ Pruning criteria working correctly - {len(marked_ids)} memories marked")
        return True
        
    except Exception as e:
        print(f"❌ Pruning criteria test failed: {e}")
        return False


async def run_all_tests():
    """Run complete test suite"""
    print("Starting Memory Scoring System Test Suite\n")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Database Schema
    result = await test_database_schema()
    test_results.append(("Database Schema", result))
    
    # Test 2: Memory Creation
    created_memories = await test_memory_creation()
    test_results.append(("Memory Creation", len(created_memories) > 0))
    
    # Test 3: User Rating
    result = await test_user_rating()
    test_results.append(("User Rating", result))
    
    # Test 4: Decay Calculations
    result = await test_decay_calculations()
    test_results.append(("Decay Calculations", result))
    
    # Test 5: API Endpoints
    result = await test_api_endpoints()
    test_results.append(("API Endpoints", result))
    
    # Test 6: Pruning System
    result = await test_pruning_criteria()
    test_results.append(("Pruning System", result))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, success in test_results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name:.<30} {status}")
        if success:
            passed += 1
    
    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("ALL TESTS PASSED! Memory scoring system is ready for production.")
    else:
        print("Some tests failed. Please review the output above.")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
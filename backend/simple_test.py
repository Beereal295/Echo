#!/usr/bin/env python3
"""
Simple test for memory scoring system
"""
import asyncio
import sqlite3
from pathlib import Path
import sys

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))


async def test_basic_functionality():
    """Test basic functionality"""
    print("Testing Memory Scoring System...")
    
    try:
        # Test 1: Check database schema
        print("1. Checking database schema...")
        db_path = Path(__file__).parent / "echo.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("PRAGMA table_info(agent_memories)")
        columns = [column[1] for column in cursor.fetchall()]
        
        new_columns = ['base_importance_score', 'user_rated', 'llm_processed']
        missing = [col for col in new_columns if col not in columns]
        
        if missing:
            print(f"   FAIL: Missing columns: {missing}")
            return False
        else:
            print("   PASS: All required columns present")
        
        conn.close()
        
        # Test 2: Import and create memory service
        print("2. Testing memory service import...")
        from app.services.memory_service import MemoryService
        from app.db.database import db
        
        await db.connect()
        memory_service = MemoryService()
        print("   PASS: Memory service created successfully")
        
        # Test 3: Test rule-based scoring
        print("3. Testing rule-based scoring...")
        test_text = "My name is John and I work as a developer"
        score = memory_service._calculate_importance(test_text)
        memory_type = memory_service._classify_memory_type(test_text)
        
        if 2.0 <= score <= 5.0:
            print(f"   PASS: Score {score} is in valid range for type '{memory_type}'")
        else:
            print(f"   FAIL: Score {score} is out of range")
            return False
        
        # Test 4: Test memory creation
        print("4. Testing memory creation...")
        memory_data = {
            'content': test_text,
            'memory_type': memory_type,
            'key_entities': memory_service._extract_entities(test_text),
            'base_importance_score': score,
            'final_importance_score': score,
            'score_source': 'rule'
        }
        
        memory_id = await memory_service.store_memory(memory_data)
        if memory_id:
            print(f"   PASS: Memory created with ID {memory_id}")
        else:
            print("   FAIL: Memory creation failed")
            return False
        
        # Test 5: Test user rating
        print("5. Testing user rating...")
        success = await memory_service.rate_memory(memory_id, 2)
        if success:
            print("   PASS: User rating applied successfully")
            
            # Verify rating was stored
            memory = await db.fetch_one("SELECT * FROM agent_memories WHERE id = ?", (memory_id,))
            if memory['user_rated'] == 1 and memory['user_score_adjustment'] == 2:
                print("   PASS: Rating stored correctly")
            else:
                print("   FAIL: Rating not stored correctly")
                return False
        else:
            print("   FAIL: User rating failed")
            return False
        
        # Test 6: Test decay calculation
        print("6. Testing decay calculations...")
        score_data = memory_service.calculate_effective_score(dict(memory))
        if 'score' in score_data and 'breakdown' in score_data:
            print(f"   PASS: Effective score calculated: {score_data['score']:.2f}")
            print(f"   Breakdown: {score_data['breakdown']}")
        else:
            print("   FAIL: Decay calculation failed")
            return False
        
        # Test 7: Test unrated memories query
        print("7. Testing unrated memories query...")
        unrated = await memory_service.get_unrated_memories(5)
        print(f"   PASS: Found {len(unrated)} memories for review")
        
        print("\nALL BASIC TESTS PASSED!")
        print("Memory scoring system is working correctly.")
        return True
        
    except Exception as e:
        print(f"ERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
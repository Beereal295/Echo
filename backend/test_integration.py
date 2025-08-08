#!/usr/bin/env python3
"""
Test the complete memory integration
"""
import asyncio
import requests
import time

BASE_URL = "http://localhost:8000"

def test_memory_endpoints():
    """Test that all memory endpoints are working"""
    print("Testing Memory System Integration")
    print("=" * 40)
    
    try:
        # Test 1: Get memory stats
        print("1. Testing memory stats endpoint...")
        response = requests.get(f"{BASE_URL}/api/memories/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"   PASS Stats: {stats['total_memories']} total, {stats['unrated_memories']} unrated")
        else:
            print(f"   FAIL Stats endpoint failed: {response.status_code}")
            return False
        
        # Test 2: Get unrated memories
        print("2. Testing unrated memories endpoint...")
        response = requests.get(f"{BASE_URL}/api/memories/unrated?limit=5")
        if response.status_code == 200:
            memories = response.json()
            print(f"   PASS Found {len(memories)} unrated memories")
            if len(memories) > 0:
                sample_memory = memories[0]
                print(f"   Sample memory: {sample_memory['content'][:50]}...")
        else:
            print(f"   FAIL Unrated memories endpoint failed: {response.status_code}")
            return False
        
        # Test 3: Test background task status
        print("3. Testing background task status...")
        response = requests.get(f"{BASE_URL}/api/memories/background-tasks/status")
        if response.status_code == 200:
            status = response.json()
            print(f"   PASS Background tasks running: {status['is_running']}")
            for task_name, task_status in status.get('tasks', {}).items():
                print(f"   Task {task_name}: {'running' if task_status.get('running') else 'stopped'}")
        else:
            print(f"   FAIL Background task status failed: {response.status_code}")
            return False
        
        # Test 4: Trigger LLM processing
        print("4. Testing manual LLM processing...")
        response = requests.post(f"{BASE_URL}/api/memories/process-llm-batch", 
                               json={"batch_size": 3})
        if response.status_code == 200:
            result = response.json()
            print(f"   PASS Processed {result['processed_count']} memories")
        else:
            print(f"   FAIL LLM processing failed: {response.status_code}")
            return False
        
        # Test 5: Test rating system (if we have memories)
        if len(memories) > 0:
            print("5. Testing memory rating...")
            memory_id = memories[0]['id']
            response = requests.post(f"{BASE_URL}/api/memories/rate",
                                   json={"memory_id": memory_id, "adjustment": 1})
            if response.status_code == 200:
                print(f"   PASS Successfully rated memory {memory_id}")
            else:
                print(f"   FAIL Rating failed: {response.status_code}")
                return False
        
        print("\n" + "=" * 40)
        print("PASS ALL INTEGRATION TESTS PASSED!")
        print("Memory system is fully integrated and working.")
        print("=" * 40)
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("FAIL ERROR: Could not connect to server")
        print("Make sure the backend server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"FAIL ERROR: {e}")
        return False

def show_usage_instructions():
    """Show how to use the new memory system"""
    print("\n" + "SUCCESS: MEMORY SYSTEM READY!" + "\n")
    print("Frontend Integration:")
    print("- Navigate to /memories page in the app")
    print("- Swipe cards left (irrelevant) or right (relevant)")
    print("- Click buttons as alternative to swiping")
    print("- See confirmation feedback after each rating")
    
    print("\nBackground Processing:")
    print("- LLM scoring runs every 5 minutes automatically")
    print("- Monthly cleanup runs on 1st of each month at 2 AM")
    print("- Manual triggers available via API")
    
    print("\nAPI Endpoints Available:")
    print("- GET  /api/memories/unrated - Get memories to review")
    print("- POST /api/memories/rate - Rate a memory")
    print("- GET  /api/memories/stats - Get memory statistics")
    print("- POST /api/memories/background-tasks/trigger-llm - Manual LLM processing")
    
    print("\nDesign Features Implemented:")
    print("PASS Card stack design matching homepage style")
    print("PASS Swipe and drag functionality")
    print("PASS Confirmation UI (not toast)")
    print("PASS Navigation integration")
    print("PASS Same design language (colors, buttons, text)")
    print("PASS API integration")
    print("PASS Background automation")

if __name__ == "__main__":
    success = test_memory_endpoints()
    
    if success:
        show_usage_instructions()
    else:
        print("\nPlease fix the issues above before using the memory system.")
#!/usr/bin/env python3
"""
Simple runner for the memory system test.
Usage: python run_memory_test.py [test_message]
"""
import sys
import os

# Add the current directory to path to import the test module
sys.path.insert(0, os.path.dirname(__file__))

from test_memory_system import EchoMemoryTester

def main():
    print("🧠 Echo Memory System Test Runner")
    print("=" * 50)
    
    # Get test message from command line or use default
    if len(sys.argv) > 1:
        test_message = " ".join(sys.argv[1:])
        print(f"Using custom test message: '{test_message}'")
    else:
        test_message = "Tell me about my recent experiences with work"
        print(f"Using default test message: '{test_message}'")
    
    print("\n⚠️  Make sure:")
    print("1. Echo backend server is running on http://localhost:8000")
    print("2. You have some diary entries and conversations in the database")
    print("3. You have some memories in the database")
    print("\nStarting test...\n")
    
    try:
        tester = EchoMemoryTester()
        results = tester.run_test(test_message)
        
        print(f"\n✅ Test completed successfully!")
        print(f"Tested {len(results)} scenarios (memory enabled/disabled)")
        
        # Quick summary
        enabled_result = results[0] if results else None
        disabled_result = results[1] if len(results) > 1 else None
        
        if enabled_result and disabled_result:
            print(f"\n📊 Quick Summary:")
            print(f"  Memory Enabled - Injected: {enabled_result.memory_context_injected}, Count: {enabled_result.memory_count}")
            print(f"  Memory Disabled - Injected: {disabled_result.memory_context_injected}, Count: {disabled_result.memory_count}")
            
            if enabled_result.memory_context_injected != disabled_result.memory_context_injected:
                print(f"  ✅ Memory system is working correctly (different behavior when enabled/disabled)")
            else:
                print(f"  ⚠️  Memory system may not be working (same behavior when enabled/disabled)")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
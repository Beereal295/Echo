#!/usr/bin/env python3
"""
Test script to verify memory system functionality in Echo chat.

This script simulates the exact same chat flow as the UI:
1. Loads preferences (including memory_enabled setting)
2. Sends chat messages with memory_enabled parameter
3. Analyzes responses for memory usage indicators
4. Compares system prompts and memory injection between enabled/disabled states
5. Does NOT save conversations (simulates user clicking "Discard")

Requirements:
- Backend server running on http://localhost:8000
- Some existing diary entries and conversations for context
- Some existing memories in the database
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
import sys
from dataclasses import dataclass
from datetime import datetime

# API Configuration
API_BASE_URL = 'http://localhost:8000/api/v1'

@dataclass
class TestResult:
    memory_enabled: bool
    message: str
    response: str
    system_prompt_used: str
    memory_context_injected: bool
    memory_count: int
    tool_calls_made: List[Dict]
    search_queries: List[str]
    processing_phases: List[Dict]
    raw_response: Dict

class EchoMemoryTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results: List[TestResult] = []
        
    def log(self, message: str):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {message}")
        
    def get_preferences(self) -> Dict[str, Any]:
        """Load preferences - exact same as ChatModal.loadPreferences()"""
        self.log("🔧 Loading preferences...")
        
        response = self.session.get(f"{API_BASE_URL}/preferences/")
        if not response.ok:
            raise Exception(f"Failed to get preferences: {response.status_code} - {response.text}")
            
        data = response.json()
        if not data.get('success'):
            raise Exception(f"Preferences API returned error: {data.get('error')}")
            
        preferences = {}
        for pref in data['data']['preferences']:
            preferences[pref['key']] = pref['typed_value']
            
        self.log(f"✅ Loaded preferences: {list(preferences.keys())}")
        return preferences
        
    def set_memory_preference(self, enabled: bool):
        """Set memory_enabled preference"""
        self.log(f"⚙️  Setting memory_enabled to {enabled}...")
        
        response = self.session.put(
            f"{API_BASE_URL}/preferences/memory_enabled",
            json={
                'key': 'memory_enabled',
                'value': enabled,
                'value_type': 'bool',
                'description': 'Enable memory system for chat'
            }
        )
        
        if not response.ok:
            self.log(f"❌ HTTP Error: {response.status_code} - {response.text}")
            raise Exception(f"Failed to set memory preference: {response.status_code} - {response.text}")
            
        data = response.json()
        self.log(f"🔧 API Response: {data}")
        
        # Check if this is a PreferenceResponse (success) or error response
        if 'key' in data and 'typed_value' in data:
            # This is a successful PreferenceResponse
            self.log(f"✅ Memory preference set to {enabled}: {data.get('typed_value')}")
        elif 'detail' in data:
            # This is an HTTPException error response
            error_msg = data.get('detail')
            self.log(f"❌ API Error: {error_msg}")
            raise Exception(f"Set preference API returned error: {error_msg}")
        else:
            # Unknown response format
            self.log(f"❌ Unexpected API response format: {data}")
            raise Exception(f"Unexpected API response format: {data}")
        
    def send_chat_message(self, message: str, memory_enabled: bool, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Send chat message - exact same as ChatModal.handleSendMessage()"""
        self.log(f"💬 Sending message: '{message[:50]}...' (memory_enabled={memory_enabled})")
        
        # Prepare request exactly like ChatModal, but with debug mode enabled
        request_data = {
            'message': message,
            'conversation_history': conversation_history or [],
            'conversation_id': None,  # Not continuing existing conversation
            'memory_enabled': memory_enabled,
            'debug_mode': True  # Enable debug mode for testing
        }
        
        self.log(f"📤 Request payload: {json.dumps(request_data, indent=2)}")
        
        response = self.session.post(
            f"{API_BASE_URL}/diary/chat",
            json=request_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if not response.ok:
            raise Exception(f"Chat API failed: {response.status_code} - {response.text}")
            
        data = response.json()
        if not data.get('success'):
            raise Exception(f"Chat API returned error: {data.get('error')}")
            
        # Extract response data (handle nested structure like ChatModal)
        chat_data = data['data']['data'] if 'data' in data['data'] else data['data']
        
        self.log(f"✅ Received response: {len(chat_data.get('response', ''))} chars")
        return chat_data
        
    def analyze_response(self, chat_data: Dict[str, Any], memory_enabled: bool, message: str) -> TestResult:
        """Analyze chat response for memory usage indicators"""
        self.log("🔍 Analyzing response for memory usage...")
        
        response_text = chat_data.get('response', '')
        tool_calls = chat_data.get('tool_calls_made', [])
        search_queries = chat_data.get('search_queries_used', [])
        processing_phases = chat_data.get('processing_phases', [])
        debug_info = chat_data.get('debug_info', {})
        
        # Use debug information for accurate analysis
        if debug_info:
            self.log("✅ Using debug information for analysis")
            memory_context_injected = debug_info.get('memory_context_injected', False)
            memory_count = debug_info.get('memory_count', 0)
            system_prompt_used = debug_info.get('system_prompt_used', 'Unknown')
            
            # Log detailed debug info
            self.log(f"🔧 Debug - Memory Enabled: {debug_info.get('memory_enabled')}")
            self.log(f"🔧 Debug - Memory Context: {bool(debug_info.get('memory_context'))}")
            self.log(f"🔧 Debug - Memory Count: {memory_count}")
            self.log(f"🔧 Debug - Tool Calls: {debug_info.get('tool_calls_count', 0)}")
            
        else:
            self.log("⚠️  No debug information available, using fallback analysis")
            # Fallback analysis (original logic)
            memory_context_injected = False
            memory_count = 0
            system_prompt_used = f"{'WITH' if memory_enabled else 'WITHOUT'}_MEMORY (inferred, no debug info)"
            
            for phase in processing_phases:
                phase_msg = phase.get('message', '').lower()
                if 'memory' in phase_msg or 'remember' in phase_msg:
                    memory_context_injected = True
                    self.log(f"🧠 Memory activity detected in phase: {phase['message']}")
            
        result = TestResult(
            memory_enabled=memory_enabled,
            message=message,
            response=response_text,
            system_prompt_used=system_prompt_used,
            memory_context_injected=memory_context_injected,
            memory_count=memory_count,
            tool_calls_made=tool_calls,
            search_queries=search_queries,
            processing_phases=processing_phases,
            raw_response=chat_data
        )
        
        self.log(f"📊 Analysis complete - Memory injected: {memory_context_injected}, Count: {memory_count}")
        return result
        
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get current memory statistics"""
        self.log("📈 Getting memory statistics...")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/memories/stats")
            if response.ok:
                data = response.json()
                if data.get('success'):
                    stats = data['data']
                    self.log(f"✅ Memory stats: {stats['total_memories']} total, {stats['unrated_memories']} unrated")
                    return stats
                else:
                    self.log(f"⚠️  Memory stats API returned: {data}")
            else:
                self.log(f"⚠️  Memory stats API failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log(f"⚠️  Memory stats error: {e}")
        
        return {}
        
    def run_test(self, test_message: str = "Tell me about my recent experiences with work") -> List[TestResult]:
        """Run complete memory test with both enabled and disabled states"""
        self.log("🚀 Starting memory system test")
        self.log("=" * 60)
        
        results = []
        
        # Get initial memory stats
        memory_stats = self.get_memory_stats()
        
        # Test with memory ENABLED
        self.log("\n" + "="*60)
        self.log("🧠 TESTING WITH MEMORY ENABLED")
        self.log("="*60)
        
        # Set preference and confirm it worked
        try:
            self.set_memory_preference(True)
            self.log("✅ Memory preference successfully set to True")
        except Exception as e:
            self.log(f"⚠️  Could not set preference (continuing anyway): {e}")
            self.log("🔧 Testing API parameter directly")
        
        chat_response = self.send_chat_message(test_message, memory_enabled=True)
        result_enabled = self.analyze_response(chat_response, True, test_message)
        results.append(result_enabled)
        
        # Wait a moment between tests
        time.sleep(2)
        
        # Test with memory DISABLED
        self.log("\n" + "="*60)
        self.log("🚫 TESTING WITH MEMORY DISABLED") 
        self.log("="*60)
        
        # Set preference and confirm it worked
        try:
            self.set_memory_preference(False)
            self.log("✅ Memory preference successfully set to False")
        except Exception as e:
            self.log(f"⚠️  Could not set preference (continuing anyway): {e}")
            self.log("🔧 Testing API parameter directly")
        
        chat_response = self.send_chat_message(test_message, memory_enabled=False)
        result_disabled = self.analyze_response(chat_response, False, test_message)
        results.append(result_disabled)
        
        # Generate comparison report
        self.log("\n" + "="*60)
        self.log("📋 TEST RESULTS COMPARISON")
        self.log("="*60)
        
        self.generate_comparison_report(result_enabled, result_disabled)
        
        return results
        
    def generate_comparison_report(self, enabled_result: TestResult, disabled_result: TestResult):
        """Generate detailed comparison report"""
        
        print("\n📊 MEMORY SYSTEM TEST REPORT")
        print("="*80)
        
        print(f"\n🧠 MEMORY ENABLED TEST:")
        print(f"   Memory Setting: {enabled_result.memory_enabled}")
        print(f"   System Prompt: {enabled_result.system_prompt_used}")
        print(f"   Memory Context Injected: {enabled_result.memory_context_injected}")
        print(f"   Tool Calls Made: {len(enabled_result.tool_calls_made)}")
        print(f"   Search Queries: {len(enabled_result.search_queries)}")
        print(f"   Processing Phases: {len(enabled_result.processing_phases)}")
        print(f"   Response Length: {len(enabled_result.response)} characters")
        
        print(f"\n🚫 MEMORY DISABLED TEST:")
        print(f"   Memory Setting: {disabled_result.memory_enabled}")
        print(f"   System Prompt: {disabled_result.system_prompt_used}")
        print(f"   Memory Context Injected: {disabled_result.memory_context_injected}")
        print(f"   Tool Calls Made: {len(disabled_result.tool_calls_made)}")
        print(f"   Search Queries: {len(disabled_result.search_queries)}")
        print(f"   Processing Phases: {len(disabled_result.processing_phases)}")
        print(f"   Response Length: {len(disabled_result.response)} characters")
        
        print(f"\n🔍 DETAILED COMPARISON:")
        
        # Compare system prompts (FULL PROMPTS)
        print(f"\n🎯 FULL SYSTEM PROMPT COMPARISON:")
        print("="*80)
        enabled_debug = enabled_result.raw_response.get('debug_info', {})
        disabled_debug = disabled_result.raw_response.get('debug_info', {})
        
        print(f"🧠 MEMORY ENABLED System Prompt:")
        enabled_prompt = enabled_debug.get('system_prompt_used', enabled_result.system_prompt_used)
        print(f"{enabled_prompt}")
        
        print(f"\n🚫 MEMORY DISABLED System Prompt:")
        disabled_prompt = disabled_debug.get('system_prompt_used', disabled_result.system_prompt_used)  
        print(f"{disabled_prompt}")
        
        print("\n" + "="*80)
        
        # Memory injection analysis
        print(f"\n🧠 MEMORY INJECTION ANALYSIS:")
        print(f"   ENABLED - Memory Retrieval Attempted: {enabled_debug.get('memory_retrieval_attempted', 'Unknown')}")
        print(f"   ENABLED - Memory Count Retrieved: {enabled_debug.get('memory_count', 'Unknown')}")
        print(f"   ENABLED - Memory Context Injected: {enabled_debug.get('memory_context_injected', 'Unknown')}")
        print(f"   DISABLED - Memory Retrieval Attempted: {disabled_debug.get('memory_retrieval_attempted', 'Unknown')}")
        print(f"   DISABLED - Memory Count Retrieved: {disabled_debug.get('memory_count', 'Unknown')}")  
        print(f"   DISABLED - Memory Context Injected: {disabled_debug.get('memory_context_injected', 'Unknown')}")
        
        # Show memory context if available
        if enabled_debug.get('memory_context'):
            print(f"\n🔍 ACTUAL MEMORY CONTEXT (ENABLED only):")
            print("-" * 40)
            print(enabled_debug['memory_context'])
            print("-" * 40)
        
        # Compare responses
        print(f"\n📝 Response Comparison:")
        print(f"   Enabled Response:  '{enabled_result.response[:100]}...'")
        print(f"   Disabled Response: '{disabled_result.response[:100]}...'")
        
        # Compare tool calls
        print(f"\n🛠️  Tool Calls Comparison:")
        if enabled_result.tool_calls_made:
            print("   ENABLED tool calls:")
            for i, call in enumerate(enabled_result.tool_calls_made):
                print(f"     {i+1}. {call.get('tool', 'unknown')} - {str(call.get('arguments', {}))[:50]}...")
        else:
            print("   ENABLED: No tool calls made")
            
        if disabled_result.tool_calls_made:
            print("   DISABLED tool calls:")
            for i, call in enumerate(disabled_result.tool_calls_made):
                print(f"     {i+1}. {call.get('tool', 'unknown')} - {str(call.get('arguments', {}))[:50]}...")
        else:
            print("   DISABLED: No tool calls made")
        
        # Compare processing phases
        print(f"\n⚙️  Processing Phases Comparison:")
        print("   ENABLED phases:")
        for i, phase in enumerate(enabled_result.processing_phases):
            print(f"     {i+1}. {phase.get('message', 'Unknown phase')}")
            
        print("   DISABLED phases:")
        for i, phase in enumerate(disabled_result.processing_phases):
            print(f"     {i+1}. {phase.get('message', 'Unknown phase')}")
            
        # Key differences
        print(f"\n🎯 KEY DIFFERENCES:")
        
        memory_diff = enabled_result.memory_context_injected != disabled_result.memory_context_injected
        print(f"   Memory Context Injection Different: {memory_diff}")
        
        tool_diff = len(enabled_result.tool_calls_made) != len(disabled_result.tool_calls_made)
        print(f"   Tool Call Count Different: {tool_diff}")
        
        response_diff = enabled_result.response != disabled_result.response
        print(f"   Response Content Different: {response_diff}")
        
        print(f"\n✅ TEST COMPLETE")
        print("="*80)

def main():
    """Run the memory system test"""
    try:
        tester = EchoMemoryTester()
        
        # You can customize the test message
        test_messages = [
            "Tell me about my recent experiences with work",
            "What did I mention about my friends recently?", 
            "How have I been feeling lately?",
            "What projects have I been working on?"
        ]
        
        print("🎯 Echo Memory System Test")
        print("This script tests if memory is being used correctly in chat sessions")
        print("It simulates the exact same flow as the UI but doesn't save conversations")
        print()
        print("🔧 NOTE: This test focuses on the memory_enabled API parameter")
        print("   The preference setting is tested but not required for core functionality")
        print()
        
        # Run test with first message
        results = tester.run_test(test_messages[0])
        
        print(f"\n🎉 Testing complete! Ran {len(results)} test cases.")
        print("Check the detailed comparison above to see if memory system is working correctly.")
        
        # Restore memory to enabled state
        tester.log("\n🔧 Attempting to restore memory_enabled to True...")
        try:
            tester.set_memory_preference(True)
        except Exception as e:
            tester.log(f"⚠️  Could not restore preference (this is okay): {e}")
            tester.log("ℹ️  You can manually enable memory in Echo settings if needed")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
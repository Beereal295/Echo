# Memory System Test Scripts

## Overview

These test scripts verify that the memory toggle system is working correctly in Echo's chat functionality. They simulate the exact same API flow as the UI but with debug information to analyze memory usage.

## Files

- `test_memory_system.py` - Comprehensive memory system test
- `run_memory_test.py` - Simple test runner
- `MEMORY_TEST_README.md` - This documentation

## Requirements

1. **Backend Server**: Echo backend must be running on `http://localhost:8000`
2. **Data**: You need some existing:
   - Diary entries in the database
   - Conversations in the database  
   - Memories in the agent_memories table
3. **Python**: Python 3.7+ with `requests` library

## Quick Test

```bash
# Run with default message
python run_memory_test.py

# Run with custom message
python run_memory_test.py "What did I write about my friends recently?"
```

## What the Test Does

1. **Sets memory preference to TRUE**
   - Loads user preferences
   - Sends a chat message with `memory_enabled=True`
   - Analyzes response for memory usage

2. **Sets memory preference to FALSE**  
   - Updates memory preference to disabled
   - Sends the same chat message with `memory_enabled=False`
   - Analyzes response (should have no memory injection)

3. **Compares Results**
   - System prompts used (with/without memory section)
   - Memory context injection (present/absent)
   - Memory count retrieved
   - Tool calls made
   - Response differences

4. **Does NOT save conversations** (simulates clicking "Discard")

## Expected Results

### When Memory is ENABLED:
- `memory_enabled: true` in debug info
- System prompt includes: `"Also check the 'What you remember about the user' section below for relevant memories"`
- `memory_context_injected: true` 
- `memory_count > 0` (if memories exist)
- Memory context appended to system prompt

### When Memory is DISABLED:
- `memory_enabled: false` in debug info  
- System prompt: `"Look for tool results containing user's journal entries and conversations. Analyze this information..."`
- `memory_context_injected: false`
- `memory_count: 0`
- No memory context in system prompt

## Debug Information

The test uses a special `debug_mode=true` parameter that returns additional information:

```json
{
  "memory_enabled": true/false,
  "system_prompt_used": "Full system prompt text...",
  "memory_context_injected": true/false,
  "memory_count": 5,
  "memory_context": "## What you remember about the user:\n...",
  "tool_calls_count": 2,
  "has_tool_calls": true,
  "timestamp": "2024-01-15 10:30:45"
}
```

## Troubleshooting

### "Connection refused" error
- Make sure Echo backend is running: `python -m app.main`
- Check if port 8000 is available

### "No memories to test" 
- Add some diary entries first
- Wait for background memory extraction to run
- Check `agent_memories` table in database

### "Same behavior for enabled/disabled"
- Check that preference is actually being saved
- Verify backend is using the session-level memory_enabled parameter
- Check logs for memory retrieval attempts

### "Empty responses"
- Ensure you have searchable diary entries
- Check Ollama is running and accessible
- Verify search tools are working

## Manual Verification

You can also manually verify by:

1. Setting memory to ON in Echo settings
2. Starting a chat with "Tell me about my work experiences"  
3. Checking browser dev tools for the API request body
4. Setting memory to OFF and repeating
5. Comparing the request bodies and responses

## Technical Details

The test simulates the exact UI flow:

1. **Load Preferences**: `GET /api/v1/preferences/`
2. **Set Memory Setting**: `PUT /api/v1/preferences/memory_enabled`
3. **Send Chat Message**: `POST /api/v1/diary/chat` with `memory_enabled` parameter
4. **Analyze Response**: Compare debug information between enabled/disabled states

This ensures the test results match real user experience.
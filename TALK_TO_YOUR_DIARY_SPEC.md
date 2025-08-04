# Talk to Your Diary - Feature Implementation Specification

## Overview
This document provides comprehensive implementation details for the "Talk to Your Diary" conversational feature in Echo. This feature allows users to have conversations with their diary using AI through a unified chat interface with optional voice capabilities.

## Feature Requirements Summary

### Core Functionality
- **Unified conversation interface** with single modal design
- **AI-powered responses** using configured LLM with full diary search capabilities
- **Advanced semantic search integration** with date range and mood filtering via LLM tool calling
- **Flexible input methods**: Text typing, speech-to-text (WebSocket), or hotkey recording
- **Streaming TTS responses** via voice toggle (piper-tts engine with hfc_female voice and streaming during text generation)
- **AI greeting system** with 10 randomized greeting variants
- **Full conversation storage** with save/discard options and transcription management
- **Real-time processing feedback** with tool call visualization
- **Turn-based conversation** with context management
- **Conversational AI tone** (4-5 line responses, human-like interaction)

### User Experience Flow
1. User visits Talk to Your Diary page with two cards
2. Left card: "Talk to Your AI" button with voice toggle
3. Right card: Shows saved conversation transcriptions
4. Click button → Single modal opens with chat interface
5. **AI greets user with random greeting (10 variants)**
6. User can type, use mic button, or hotkey for input
7. AI processes with visual feedback, performs diary searches via tool calls
8. AI responds with streaming text generation (4-5 lines max, conversational tone)
9. If voice toggle ON: TTS plays AI response with streaming while text generates
10. Conversation continues with full diary search capabilities
11. Conversation ends with save/discard option

## Technical Architecture

### Frontend Components

#### Current State
- **File**: `frontend/src/pages/TalkToYourDiaryPage.tsx`
- **Current Content**: Placeholder with "Conversational interface coming soon..."
- **Status**: Needs complete implementation

#### Required Components - SIMPLIFIED DESIGN

1. **Main Page Layout**
   - Two cards side-by-side
   - Left card: Single "Talk to Your AI" button + voice toggle
   - Right card: Saved transcriptions list with badges
   - Voice toggle syncs between main page and modal
   - Toggle preference saved in database

2. **Unified Chat Modal**
   - Single modal for all conversations
   - WhatsApp-style chat bubbles (user left, AI right)
   - Voice toggle at top of modal (synced with main page)
   - Mic button next to input field (click-to-speak, click-to-stop)
   - Processing indicator above input (typing animation style)
   - Tool calls shown in green text, normal processing in gray
   - End Chat button (prominent placement)

3. **Save/Discard Modal**
   - Shows complete conversation transcription
   - Save/Discard buttons
   - Appears after "End Chat" button
   - Auto-saves if user closes modal with X button

### Backend Integration

#### Existing APIs to Leverage

1. **Enhanced Semantic Search API** ✅ IMPLEMENTED
   - **Endpoint**: `POST /api/v1/embeddings/semantic-search`
   - **Enhanced Request Schema**: 
     ```typescript
     {
       query: string,
       limit: number,
       similarity_threshold: number,
       date_range?: { start_date: string, end_date: string },
       mood_tags?: string[]
     }
     ```
   - **Usage**: Exclusively for LLM tool calling (not frontend search)

2. **WebSocket STT Integration**
   - **File**: `frontend/src/lib/websocket.ts`
   - **WebSocket URL**: `ws://localhost:8000/api/v1/ws/stt`
   - **Implementation**: Copy exact integration from NewEntryPage
   - **Behavior**: STT results appear in input box for editing before sending

3. **Settings Integration**
   - **Voice Toggle Preference**: Save in preferences table
   - **Hotkey Support**: Use existing hotkey configuration
   - **Ollama Model**: Use configured LLM model from settings

#### New APIs Implemented ✅

1. **TTS Service API** ✅ IMPLEMENTED
   - **Endpoint**: `POST /api/v1/tts/synthesize`
   - **Request**: `{ text: string, voice: string, stream: boolean }`
   - **Response**: Streaming audio (ready for piper-tts integration with hfc_female voice)

2. **Diary Chat API** ✅ IMPLEMENTED
   - **Endpoint**: `POST /api/v1/diary/chat`
   - **Request**: `{ message: string, conversation_history?: array }`
   - **Response**: `{ response: string, tool_calls_made: array, search_queries_used: array }`
   - **Features**: Ollama function calling with search_diary tool

3. **Search Feedback API** ✅ IMPLEMENTED
   - **Endpoint**: `GET /api/v1/diary/search-feedback`
   - **Response**: Random friendly processing messages
   - **Usage**: Display during tool calling (green text)

4. **Greeting API** ✅ IMPLEMENTED
   - **Endpoint**: `GET /api/v1/diary/greeting`
   - **Response**: Random greeting message (1 of 10 variants)
   - **Usage**: First AI bubble when modal opens

5. **Conversation Management APIs** ✅ IMPLEMENTED
   - **POST /api/v1/conversations**: Create/save conversations
   - **GET /api/v1/conversations**: List saved conversations
   - **DELETE /api/v1/conversations/{id}**: Delete conversations
   - **GET /api/v1/conversations/stats**: Conversation statistics

## Implementation Details

### Conversation Flow

#### Single Modal Approach
1. **Initialization**: Modal opens with fresh conversation (no previous context)
2. **Input Methods**: 
   - Text typing in input field
   - Mic button (click-to-speak, click-to-stop) - results appear in input for editing
   - Hotkey recording (F8 default) - results appear in input for editing
3. **Processing**: Visual feedback above input with typing animation
4. **AI Response**: Chat bubble with optional TTS playback if toggle enabled
5. **End Conversation**: Prominent "End Chat" button or X button (auto-save)

#### AI Greeting System
**Purpose**: Welcome users with randomized, friendly greetings to avoid repetitive interactions

**10 Greeting Variants** (randomly selected on modal open):
1. "Hi there! I'm Echo, your diary companion. You can type your thoughts or use the voice button to talk with me. What's on your mind today?"
2. "Hello! Echo here, ready to help you explore your diary. Feel free to type or speak - I'm listening. How can I assist you?"
3. "Hey! I'm Echo, and I'm here to chat about your journal entries. You can write or use voice - whatever feels comfortable. What would you like to discuss?"
4. "Hi! It's Echo, your personal diary AI. Type away or hit the mic button to speak with me. What are you curious about from your entries?"
5. "Hello there! I'm Echo, ready to dive into your diary with you. Use text or voice - I'm here either way. What's something you'd like to explore?"
6. "Hey! Echo at your service, ready to chat about your journal. Type your questions or speak them aloud - I'm all ears. What shall we talk about?"
7. "Hi! I'm Echo, your diary conversation partner. Whether you type or talk, I'm here to help. What memories or thoughts would you like to revisit?"
8. "Hello! Echo here, excited to explore your diary together. Use the keyboard or microphone - both work great. What's something interesting you'd like to find?"
9. "Hey there! I'm Echo, and I love helping you discover insights from your entries. Type or speak your thoughts - I'm ready. What's on your agenda today?"
10. "Hi! It's Echo, your journal AI companion. Feel free to type or use voice input - whatever suits you best. What would you like to uncover from your diary?"

**Implementation**:
- Greeting appears as first AI bubble when modal opens
- Random selection from 10 variants using frontend randomization
- If voice toggle is ON: Greeting is read aloud via TTS
- Greeting sets conversational, welcoming tone for interaction

#### Processing Indicators
- **Tool Calls**: Green text with messages like "Searching your diary..." with typing animation
- **Normal Processing**: Gray text with "Processing..." with typing animation  
- **Animation**: WhatsApp-style typing dots animation above input field
- **Streaming Response**: Text appears progressively as AI generates response
- **Voice Streaming**: TTS plays while text is still being generated (streaming audio)

#### Voice Toggle Behavior
- **Location**: Main page + modal top (synced)
- **Storage**: Saved in preferences table
- **Function**: Controls TTS playback of AI responses
- **Default**: User's last preference (or OFF for first time)

### LLM Integration with Function Calling

#### AI System Prompt and Behavior Rules
**Conversational Guidelines for Echo:**
- **Response Length**: Maximum 4-5 lines per response to maintain chat-like flow
- **Tone**: Human-like, warm, and conversational (not mechanical or robotic)
- **Personality**: Gentle, understanding diary companion named Echo
- **Context Awareness**: Use diary search results naturally in conversation
- **Engagement**: Ask follow-up questions when appropriate
- **Memory**: Reference previous messages within the same conversation session

**System Prompt for LLM**:
```
You are Echo, a gentle and conversational diary companion. You help users explore their thoughts and memories by searching through their journal entries when needed.

IMPORTANT GUIDELINES:
- Keep responses to 4-5 lines maximum for natural chat flow
- Be human-like, warm, and conversational (never mechanical)
- Use the search_diary tool when users ask about past experiences, memories, patterns, or specific topics
- Naturally weave search results into your responses
- Ask follow-up questions to encourage deeper reflection
- Speak in first person as Echo, their trusted diary companion
- Be supportive and understanding, never judgmental

When users ask questions about their past, use search_diary with relevant keywords, dates, or mood filters to find entries that can inform your response.
```

#### Ollama Function Calling ✅ IMPLEMENTED
The implementation uses Ollama's native function calling with Mistral models for diary search integration:

**Tool Definition**:
```json
{
  "type": "function",
  "function": {
    "name": "search_diary",
    "description": "Search user's diary entries by content, date, mood, or people",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {"type": "string", "description": "Text content to search for"},
        "date_range": {
          "type": "object", 
          "properties": {
            "start_date": {"type": "string", "format": "date"},
            "end_date": {"type": "string", "format": "date"}
          }
        },
        "mood_tags": {"type": "array", "items": {"type": "string"}},
        "limit": {"type": "integer", "default": 5}
      },
      "required": ["query"]
    }
  }
}
```

**Ollama Request Format**:
```json
{
  "model": "mistral",
  "prompt": "[INST] System prompt with conversation context [/INST]",
  "tools": [search_diary_tool],
  "raw": true
}
```

**Expected Response**:
```json
{
  "response": "Let me search your diary... [TOOL_CALLS] [{\"name\": \"search_diary\", \"arguments\": {\"query\": \"work stress\"}}]",
  "done": true
}
```

### Database Schema ✅ IMPLEMENTED

#### Conversations Table
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    duration INTEGER DEFAULT 0,  -- in seconds
    transcription TEXT NOT NULL,
    conversation_type TEXT NOT NULL,  -- Always 'chat' for unified design
    message_count INTEGER DEFAULT 0,
    search_queries_used TEXT,  -- JSON array
    created_at DATETIME NOT NULL,
    updated_at DATETIME
);
```

#### Preferences Integration
Voice toggle preference will be stored in existing preferences table:
```sql
-- Add to existing preferences
voice_enabled BOOLEAN DEFAULT 0
```

### Frontend State Management

#### Conversation State (No Context Between Sessions)
- Each modal session starts fresh
- No conversation history maintained between modal opens
- Users can save conversations before closing if they want to reference later

#### Voice Toggle State
- Synced between main page and modal
- Persisted in preferences table
- Applied immediately when toggled

#### Processing State
- Show processing indicators during AI responses
- Different styling for tool calls vs normal processing
- Typing animation similar to WhatsApp

## API Integration Examples

### Frontend API Usage
```typescript
// Modal initialization - get random greeting
const greeting = await api.getDiaryGreeting();

// Show greeting as first AI bubble
addAIMessage(greeting.data);

// If voice toggle ON: play greeting audio
if (voiceEnabled) {
  const audioBlob = await api.synthesizeSpeech(greeting.data, 'hfc_female', true);
  // Stream audio while greeting text appears
}

// Chat message processing
const response = await api.diaryChatMessage(message, conversationHistory);

// Show processing feedback during AI response
const feedback = await api.getSearchFeedback();
showProcessingIndicator(feedback.data, response.tool_calls_made.length > 0);

// Handle streaming response
if (response.response) {
  // Stream text into chat bubble (typewriter effect)
  streamTextToChat(response.response);
  
  // If voice toggle ON: stream TTS simultaneously
  if (voiceEnabled) {
    const audioStream = await api.synthesizeSpeech(response.response, 'hfc_female', true);
    playStreamingAudio(audioStream);
  }
}

// Save conversation on end
await api.createConversation({
  transcription: fullTranscription,
  conversation_type: 'chat',
  duration: conversationDuration,
  message_count: messageCount,
  search_queries_used: allSearchQueries
});
```

### Processing Flow
1. User sends message via typing, mic button, or hotkey
2. Show processing indicator with typing animation and random feedback message
3. If AI uses tools: Show green "Searching your diary..." text with animation
4. If normal processing: Show gray "Processing..." text with animation
5. AI responds with streaming text generation (text appears progressively in chat bubble)
6. If voice toggle ON: TTS plays simultaneously while text is still generating (streaming audio)
7. Response completes with full text visible and audio finished
8. Repeat conversation turns until user clicks "End Chat"

### Streaming Requirements
- **Text Streaming**: AI responses appear progressively as they're generated (typewriter effect)
- **Voice Streaming**: TTS audio plays while text is still being generated (don't wait for complete text)
- **Processing Feedback**: Real-time status updates during tool calls and processing
- **Responsive UI**: All interactions remain responsive during streaming operations

## Updated Implementation Priority

### Phase 1: Core Modal (HIGHEST PRIORITY)
1. Single modal with chat interface
2. Basic text input and AI response
3. Voice toggle integration
4. End chat functionality

### Phase 2: Enhanced Input (HIGH PRIORITY)
1. Mic button integration (copy from NewEntryPage)
2. STT results in input box for editing
3. Hotkey support
4. Processing indicators with animations

### Phase 3: Polish (MEDIUM PRIORITY)
1. Save/discard modal
2. Transcription display in right panel
3. Voice toggle preference persistence
4. Error handling and recovery

This simplified design eliminates the complexity of separate call/chat modes while maintaining all core functionality through a single, intuitive interface.

## Technical Notes

### Key Simplifications Made
- **Single Modal**: No separate call/chat interfaces
- **Unified Input**: One interface with multiple input methods
- **No Session Context**: Fresh start each time (users save if needed)
- **Click-to-Speak**: Simple mic button behavior like Add Entry page
- **Auto-save on X**: Reduces decision fatigue

### Backend Services Ready ✅
All backend implementation is complete and compatible with this simplified design:
- Database schema and migrations
- Enhanced semantic search for LLM tool usage
- TTS service (ready for piper-tts with hfc_female voice)
- Conversation CRUD APIs
- LLM integration with function calling
- Conversation processing service

### Frontend Development Focus
The frontend implementation is now much simpler and more focused:
- Single page with two cards
- One modal component with chat interface
- Voice toggle in two locations (synced)
- Processing indicators and animations
- Save/discard workflow

This approach provides the same functionality with significantly less complexity and better user experience.
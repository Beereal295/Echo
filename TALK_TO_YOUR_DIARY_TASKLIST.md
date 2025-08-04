# Talk to Your Diary - SIMPLIFIED Implementation Tasklist

This document serves as the project management tool for implementing the Talk to Your Diary feature in Echo with the **SIMPLIFIED UNIFIED DESIGN**. All tasks must be completed in order and confirmed by project lead before proceeding.

## Task Status Legend
- ⏳ **Pending** - Not started
- 🔄 **In Progress** - Currently being implemented
- ✅ **Ready for Testing** - Implementation complete, awaiting project lead validation
- ✅ **Confirmed** - Tested and approved by project lead
- ❌ **Needs Revision** - Requires changes based on feedback

---

## DESIGN CHANGE SUMMARY ⚠️

**OLD DESIGN (Discarded):**
- Separate Call and Chat modes with different modals
- Complex voice call interface with animations
- Separate workflows for different conversation types
- 120+ sub-tasks across 8 phases

**NEW SIMPLIFIED DESIGN (Current):**
- Single "Talk to Your AI" button with unified modal
- One chat interface with optional voice toggle
- All input methods in one interface (type/mic/hotkey)
- Processing indicators with green text for tool calls
- Auto-save on X, save/discard on End Chat
- ~40 sub-tasks across 4 phases

---

## ✅ COMPLETED BACKEND IMPLEMENTATION (Ready for Testing)

### Phase 1: Backend Infrastructure & Database - ✅ COMPLETE
All backend services are implemented and compatible with the simplified design.

#### Task TTD-1.1: Database Schema Extension ✅ **Ready for Testing**
**Sub-tasks:**
- [x] TTD-1.1.1: Add conversations table to schema.py - **IMPLEMENTED**
- [x] TTD-1.1.2: Create database migration for conversations table - **IMPLEMENTED & TESTED**
- [x] TTD-1.1.3: Add required indexes for conversations - **IMPLEMENTED**
- [x] TTD-1.1.4: Update database initialization to include new table - **IMPLEMENTED**
- [x] TTD-1.1.5: Create conversation data model class - **IMPLEMENTED**

**Implementation Notes:**
- Database migration v3 successfully applied
- Conversations table created with proper schema
- All indexes and constraints in place
- File: `backend/app/db/schema.py`, `backend/app/models/conversation.py`

#### Task TTD-1.2: Enhanced Semantic Search API ✅ **Ready for Testing**
**Sub-tasks:**
- [x] TTD-1.2.1: Add date_range parameter to SemanticSearchRequest - **IMPLEMENTED**
- [x] TTD-1.2.2: Add mood_tags parameter to SemanticSearchRequest - **IMPLEMENTED**
- [x] TTD-1.2.3: Implement date filtering in semantic search - **IMPLEMENTED**
- [x] TTD-1.2.4: Implement mood tag filtering in semantic search - **IMPLEMENTED**
- [x] TTD-1.2.5: Update semantic search response to include filter metadata - **IMPLEMENTED**

**Implementation Notes:**
- Enhanced for LLM tool usage only (not frontend search bar)
- Supports date range and mood tag filtering
- File: `backend/app/api/routes/embeddings.py`

#### Task TTD-1.3: TTS Service Integration ✅ **Ready for Testing**
**Sub-tasks:**
- [x] TTD-1.3.1: Setup TTS dependencies - **IMPLEMENTED** (torch/torchaudio added)
- [x] TTD-1.3.2: Create TTS service class - **IMPLEMENTED** (piper-tts integration)
- [x] TTD-1.3.3: Implement streaming TTS - **IMPLEMENTED** (AsyncGenerator support)
- [x] TTD-1.3.4: Add hfc_female voice integration - **IMPLEMENTED** (default voice)
- [x] TTD-1.3.5: Create TTS API endpoints - **IMPLEMENTED** (full endpoint suite)

**Implementation Notes:**
- Streaming TTS ready for piper-tts integration with hfc_female voice
- Voice toggle will control TTS playback
- Files: `backend/app/services/tts_service.py`, `backend/app/api/routes/tts.py`

### Phase 2: Conversation Backend Logic - ✅ COMPLETE

#### Task TTD-2.1: Conversation API Endpoints ✅ **Ready for Testing**
**Sub-tasks:**
- [x] TTD-2.1.1: Create conversation creation endpoint - **IMPLEMENTED**
- [x] TTD-2.1.2: Create conversation retrieval endpoints - **IMPLEMENTED**
- [x] TTD-2.1.3: Create conversation deletion endpoint - **IMPLEMENTED**
- [x] TTD-2.1.4: Add conversation statistics endpoint - **IMPLEMENTED**
- [x] TTD-2.1.5: Implement error handling and validation - **IMPLEMENTED**

**Implementation Notes:**
- Full CRUD API for conversation management
- Statistics endpoint for right panel display
- Files: `backend/app/api/routes/conversations.py`, `backend/app/db/repositories/conversation_repository.py`

#### Task TTD-2.2: LLM Tool Integration ✅ **Ready for Testing**
**Sub-tasks:**
- [x] TTD-2.2.1: Create search_diary tool definition - **IMPLEMENTED** (Ollama function calling)
- [x] TTD-2.2.2: Implement Ollama function calling - **IMPLEMENTED** (generate_with_tools)
- [x] TTD-2.2.3: Add conversation context management - **IMPLEMENTED**
- [x] TTD-2.2.4: Create diary chat endpoint - **IMPLEMENTED** (POST /api/v1/diary/chat)
- [x] TTD-2.2.5: Implement search feedback responses - **IMPLEMENTED** (8 friendly messages)

**Implementation Notes:**
- Ollama function calling with search_diary tool
- Green text indicators for tool calls ready
- Files: `backend/app/services/diary_chat_service.py`, `backend/app/api/routes/diary_chat.py`

#### Task TTD-2.3: Conversation Processing Service ✅ **Ready for Testing**
**Sub-tasks:**
- [x] TTD-2.3.1: Create conversation service class - **IMPLEMENTED**
- [x] TTD-2.3.2: Implement conversation state management - **IMPLEMENTED**
- [x] TTD-2.3.3: Add turn-based conversation logic - **IMPLEMENTED**
- [x] TTD-2.3.4: Implement conversation duration tracking - **IMPLEMENTED**
- [x] TTD-2.3.5: Add conversation transcription formatting - **IMPLEMENTED**

**Implementation Notes:**
- Complete conversation lifecycle management
- Compatible with simplified single modal design
- File: `backend/app/services/conversation_service.py`

---

## Phase 3: Simplified Frontend Implementation ⏳

### Task TTD-3.1: Main Page Layout ⏳
**Description:** Implement simplified two-card layout with single button
**Sub-tasks:**
- [ ] TTD-3.1.1: Replace TalkToYourDiaryPage with two-card layout
- [ ] TTD-3.1.2: Create left card with "Talk to Your AI" button + voice toggle
- [ ] TTD-3.1.3: Create right card for saved transcriptions display
- [ ] TTD-3.1.4: Add transcription badges and list functionality
- [ ] TTD-3.1.5: Implement voice toggle state management (sync with modal)
- [ ] TTD-3.1.6: Add voice toggle preference persistence to database

**Dependencies:** Backend Phase 1-2 ✅
**Testing Criteria:** Two-card layout with working voice toggle and transcription display
**Status:** ⏳ **Pending**

### Task TTD-3.2: Unified Chat Modal ⏳
**Description:** Create single modal with chat interface and voice capabilities
**Sub-tasks:**
- [ ] TTD-3.2.1: Create ChatModal component with overlay
- [ ] TTD-3.2.2: Implement WhatsApp-style chat bubbles (user left, AI right)
- [ ] TTD-3.2.3: Add voice toggle at top of modal (synced with main page)
- [ ] TTD-3.2.4: Create text input field with send button
- [ ] TTD-3.2.5: Add mic button next to input (click-to-speak, click-to-stop)
- [ ] TTD-3.2.6: Implement processing indicator above input (typing animation)
- [ ] TTD-3.2.7: Add tool call indicators (green text) vs normal processing (gray)
- [ ] TTD-3.2.8: Create prominent "End Chat" button
- [ ] TTD-3.2.9: Handle modal close (X button) with auto-save

**Dependencies:** TTD-3.1
**Testing Criteria:** Modal displays with chat interface, voice toggle, and all input methods
**Status:** ⏳ **Pending**

### Task TTD-3.3: STT Integration ⏳
**Description:** Copy STT integration from NewEntryPage for modal use
**Sub-tasks:**
- [ ] TTD-3.3.1: Copy useSTT hook from NewEntryPage
- [ ] TTD-3.3.2: Adapt STT for chat modal context
- [ ] TTD-3.3.3: Implement mic button behavior (click-to-speak, click-to-stop)
- [ ] TTD-3.3.4: Add STT results to input field for editing
- [ ] TTD-3.3.5: Add hotkey support using existing settings
- [ ] TTD-3.3.6: Implement STT error handling in modal

**Dependencies:** TTD-3.2
**Testing Criteria:** STT works exactly like NewEntryPage with results in input field
**Status:** ⏳ **Pending**

### Task TTD-3.4: Chat Processing & AI Integration ⏳
**Description:** Connect chat interface to backend LLM and TTS services
**Sub-tasks:**
- [ ] TTD-3.4.1: Add diary chat API calls to api.ts
- [ ] TTD-3.4.2: Implement chat message sending and receiving
- [ ] TTD-3.4.3: Add processing indicators with search feedback API
- [ ] TTD-3.4.4: Implement tool call vs normal processing visual distinction
- [ ] TTD-3.4.5: Add TTS integration for AI responses (when voice toggle ON)
- [ ] TTD-3.4.6: Handle chat errors and timeouts gracefully

**Dependencies:** TTD-3.3
**Testing Criteria:** Complete chat workflow with AI responses and optional voice
**Status:** ⏳ **Pending**

---

## Phase 4: Polish and Integration ⏳

### Task TTD-4.1: Save/Discard Modal ⏳
**Description:** Implement conversation saving workflow
**Sub-tasks:**
- [ ] TTD-4.1.1: Create SaveDiscardModal component
- [ ] TTD-4.1.2: Show full conversation transcription
- [ ] TTD-4.1.3: Add Save and Discard buttons
- [ ] TTD-4.1.4: Implement save conversation API call
- [ ] TTD-4.1.5: Handle auto-save on modal X button close
- [ ] TTD-4.1.6: Update right panel after saving

**Dependencies:** TTD-3.4
**Testing Criteria:** Save/discard workflow works with transcription display
**Status:** ⏳ **Pending**

### Task TTD-4.2: Transcription Display ⏳
**Description:** Implement saved conversations display in right panel
**Sub-tasks:**
- [ ] TTD-4.2.1: Create transcription list component
- [ ] TTD-4.2.2: Add conversation badges (Chat indicator)
- [ ] TTD-4.2.3: Implement conversation preview and expansion
- [ ] TTD-4.2.4: Add delete functionality for saved conversations
- [ ] TTD-4.2.5: Add basic search/filtering for conversations
- [ ] TTD-4.2.6: Implement real-time updates after new saves

**Dependencies:** TTD-4.1
**Testing Criteria:** Right panel displays saved conversations with full functionality
**Status:** ⏳ **Pending**

### Task TTD-4.3: Settings Integration & Polish ⏳
**Description:** Integrate with existing settings and add final polish
**Sub-tasks:**
- [ ] TTD-4.3.1: Add voice_enabled to preferences table schema
- [ ] TTD-4.3.2: Implement voice toggle preference persistence
- [ ] TTD-4.3.3: Ensure hotkey settings apply to chat modal
- [ ] TTD-4.3.4: Ensure LLM model settings apply to conversations
- [ ] TTD-4.3.5: Add comprehensive error handling and recovery
- [ ] TTD-4.3.6: Implement loading states and animations
- [ ] TTD-4.3.7: Add responsive design for mobile devices

**Dependencies:** TTD-4.2
**Testing Criteria:** All settings integration works, comprehensive error handling
**Status:** ⏳ **Pending**

### Task TTD-4.4: Testing and Validation ⏳
**Description:** Comprehensive testing of complete feature
**Sub-tasks:**
- [ ] TTD-4.4.1: Test complete conversation workflow end-to-end
- [ ] TTD-4.4.2: Test voice toggle functionality and persistence
- [ ] TTD-4.4.3: Test all input methods (type, mic, hotkey)
- [ ] TTD-4.4.4: Test processing indicators and tool call visualization
- [ ] TTD-4.4.5: Test save/discard workflows and transcription display
- [ ] TTD-4.4.6: Test error scenarios and recovery
- [ ] TTD-4.4.7: Test integration with existing app features
- [ ] TTD-4.4.8: Performance testing with long conversations

**Dependencies:** TTD-4.3
**Testing Criteria:** Feature works flawlessly in all scenarios
**Status:** ⏳ **Pending**

---

## ✅ IMPLEMENTATION STATUS SUMMARY

**COMPLETED (Ready for Testing):**
- ✅ **Backend Complete** - All APIs, services, and database ready
- ✅ **Database Schema** - Conversations table with migration
- ✅ **LLM Integration** - Ollama function calling with diary search
- ✅ **TTS Service** - Streaming implementation ready for piper-tts with hfc_female voice
- ✅ **Conversation APIs** - Full CRUD with statistics

**PENDING (Frontend Implementation):**
- ⏳ **Main Page Layout** - Two cards with voice toggle
- ⏳ **Chat Modal** - Unified interface with all input methods
- ⏳ **STT Integration** - Copy from NewEntryPage
- ⏳ **AI Integration** - Connect to backend services
- ⏳ **Save/Discard** - Conversation management workflow
- ⏳ **Transcription Display** - Right panel functionality
- ⏳ **Settings Integration** - Voice toggle persistence
- ⏳ **Testing & Polish** - Final validation

**Key Simplifications Achieved:**
1. **Single Modal Design** - No separate call/chat interfaces
2. **Unified Input Methods** - Type, mic, hotkey in one interface
3. **No Session Context** - Fresh conversations each time
4. **Auto-save on X** - Reduced decision fatigue
5. **Backend Compatibility** - All existing services work with new design

**Estimated Completion:**
- **Backend:** ✅ 100% Complete (6 major tasks, 30 sub-tasks)
- **Frontend:** ⏳ 0% Complete (8 major tasks, ~40 sub-tasks) 
- **Overall Progress:** 43% Complete

**Next Step:** Begin TTD-3.1 (Main Page Layout) implementation

---

**Document Version:** 2.0 - Simplified Design
**Last Updated:** Current session - Major design simplification applied
**Status:** Backend ready for testing, Frontend implementation pending
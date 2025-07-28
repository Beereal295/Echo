# Additional Context - STT Integration & Multi-Paragraph Recording

This document provides additional architectural context for implementing the Speech-to-Text (STT) integration and multi-paragraph recording workflow in DearDiary, based on existing STT implementation and design discussions.

## STT Integration Architecture

### FastAPI Background Service Approach

**Core Structure:**
- STT runs as a **background thread/service** within the same FastAPI process
- Single process deployment for easier packaging and management
- Dedicated endpoints for STT control and configuration
- WebSocket connection for real-time state updates and transcription results

**API Endpoints:**
```
GET /api/stt/status          # Check STT service status (ready/recording/error)
POST /api/stt/config         # Update hotkey and Whisper model settings
WebSocket /ws/stt            # Real-time state updates and transcription delivery
```

**FastAPI Process Structure:**
```
main.py
├── STT Background Service
│   ├── Whisper model (lazy loaded on first use)
│   ├── Audio capture (sounddevice integration)
│   ├── Hotkey registration (keyboard library)
│   └── State broadcasting via WebSocket
├── WebSocket handler (/ws/stt)
├── STT configuration endpoints
└── Existing journal API endpoints
```

### Configuration Management

**Database-Driven Settings:**
- Store hotkey configuration in SQLite `preferences` table (not config.json)
- Frontend settings page manages STT configuration through REST API
- Settings include:
  - Hotkey combination (default: F8)
  - Whisper model size (base/small/medium)
  - Audio input device selection
  - Enable/disable STT service

**Configuration Flow:**
1. User changes hotkey in frontend settings page
2. Frontend sends `POST /api/stt/config` with new settings
3. STT background service receives notification
4. Service re-registers hotkeys with new configuration
5. Settings persisted in database for next app launch

## Multi-Paragraph Recording Workflow

### User Experience Flow

**Recording Multiple Thoughts:**
1. User holds F8 → WebSocket sends `{"state": "recording"}`
2. User speaks first thought → Releases F8
3. WebSocket sends `{"state": "processing"}` → `{"state": "transcribing"}`
4. Transcription complete → WebSocket sends:
   ```json
   {
     "state": "complete",
     "text": "Today was a great day.",
     "append": true
   }
   ```
5. Frontend appends text to textarea: `"Today was a great day."`
6. User holds F8 again for second thought
7. New transcription appended with paragraph break:
   ```
   Today was a great day.
   
   I really enjoyed the meeting with my team.
   ```
8. Process repeats for as many thoughts as needed
9. User clicks "Create All Three Entries" when satisfied
10. **Entire textarea content** sent as unified prompt to Ollama

### Frontend Text Accumulation

**Textarea Behavior:**
- Each completed transcription **appends** to existing content
- **Double line break** (`\n\n`) automatically inserted between thoughts
- User retains full edit control over accumulated text
- Visual feedback shows recording states during each hotkey session

**Example Progressive Build-up:**
```
Thought 1: "Today was a great day."

Thought 2: "Today was a great day.

I really enjoyed the meeting with my team."

Thought 3: "Today was a great day.

I really enjoyed the meeting with my team.

Looking forward to tomorrow's presentation."
```

### LLM Processing Integration

**Unified Entry Processing:**
- Complete accumulated text sent as **single prompt** to Ollama
- All three modes (raw, enhanced, structured) process the **full multi-paragraph entry**
- LLM receives complete context for coherent processing
- Results in three comprehensive versions of the entire journal session

**Prompt Structure:**
```json
{
  "system": "You are a helpful writing assistant...",
  "prompt": "Today was a great day.\n\nI really enjoyed the meeting with my team.\n\nLooking forward to tomorrow's presentation."
}
```

## WebSocket Communication Protocol

### State Messages
```json
// Recording started
{"type": "state", "state": "recording", "message": "Recording... Release F8 to stop"}

// Processing audio
{"type": "state", "state": "processing", "message": "Processing audio..."}

// Whisper transcription
{"type": "state", "state": "transcribing", "message": "Converting speech to text..."}

// Transcription complete
{"type": "transcription", "state": "complete", "text": "Transcribed text here", "append": true}

// Error handling
{"type": "error", "message": "Transcription failed", "fallback": true}

// Service status
{"type": "status", "stt_ready": true, "model_loaded": false}
```

### Connection Management
- WebSocket connection established when New Entry page loads
- Connection maintained throughout entry creation session
- Graceful reconnection handling for network interruptions
- Connection closed when user navigates away from entry creation

## Technical Implementation Details

### Audio Processing Pipeline
**Based on Existing STT Implementation:**
- Dynamic sample rate detection: `sd.query_devices(None, 'input')`
- Real-time audio capture with `sounddevice.InputStream`
- In-memory WAV processing using `BytesIO`
- Audio resampling to 16kHz for Whisper compatibility
- Proper float32 conversion for optimal transcription quality

### Resource Management
**Lazy Loading Strategy:**
- FastAPI startup → STT service starts → Whisper model **NOT** loaded
- First recording attempt → Lazy load Whisper model → Cache in memory
- App shutdown → Clean up Whisper model and audio resources
- Memory-efficient approach for better startup performance

### Thread Safety Considerations
- STT background service runs in separate thread from FastAPI
- Thread-safe communication via queue/WebSocket mechanisms
- Hotkey registration handled in background thread
- State synchronization between recording thread and WebSocket handler

### Error Handling & Fallbacks
**Graceful Degradation:**
- STT service unavailable → Frontend shows manual text input only
- Whisper model loading fails → Error message with retry option
- Hotkey conflicts → Notification with alternative hotkey suggestion
- Audio device issues → Device selection dropdown in settings

**User Experience During Errors:**
- Clear error messages in recording popup
- Fallback to manual typing always available
- Settings page shows STT service status
- Retry mechanisms for temporary failures

## Benefits of This Architecture

### User Experience
- **Natural speech patterns:** Each recording captures one complete thought
- **Real-time feedback:** Visual states during recording and processing
- **Flexible workflow:** Mix of voice and manual text editing
- **Unified processing:** All thoughts processed together for coherent results

### Technical Advantages
- **Single process deployment:** Easier packaging and distribution
- **Real-time communication:** WebSocket for instant UI updates
- **Database-driven config:** Settings managed through UI
- **Resource efficient:** Lazy loading and proper cleanup
- **Scalable architecture:** Easy to add new STT features

### Development Benefits
- **Code reuse:** Leverages existing STT implementation
- **Clean separation:** STT service isolated from main application logic
- **Testing friendly:** Each component can be tested independently
- **Maintainable:** Clear interfaces between components

This architecture provides a solid foundation for implementing sophisticated voice-to-text functionality while maintaining the simplicity and privacy-first approach that defines DearDiary.

## Implementation Decisions & Technical Specifications

### Electron Integration Strategy

**FastAPI Process Management:**
- **Architecture:** Spawn FastAPI as a **child process** from Electron's main process
- **Benefits:** Clean separation, easier debugging, can restart FastAPI if it crashes
- **Port Management:** Use **dynamic port allocation** (find available port on startup)
- **Lifecycle:** Electron starts FastAPI on app launch, terminates it on app exit
- **Communication:** Electron frontend connects to `http://localhost:{dynamic_port}`

**Process Health Monitoring:**
- Electron monitors FastAPI health via ping endpoint (`GET /api/health`)
- Automatic FastAPI restart if process becomes unresponsive
- UI connection status indicator (green/red) in settings or status bar
- Graceful error handling when FastAPI is temporarily unavailable

### Database Management

**SQLite Storage Location:**
- **Database Path:** `app_directory/data/deardiary.db`
- **Data Directory:** All user data contained in `data/` folder for easy backup
- **Schema Migrations:** Simple version tracking in `schema_version` table
- **User Backup:** Users can copy entire `data/` folder for manual backup

**Database Schema Additions:**
```sql
-- Draft auto-save table
drafts (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Schema versioning
schema_version (
    version INTEGER PRIMARY KEY,
    applied_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Entry processing status tracking
ALTER TABLE entries ADD COLUMN status TEXT DEFAULT 'processed';
-- Values: 'draft', 'transcribed', 'processed', 'error'
```

### Ollama Integration Implementation

**Connection Detection Strategy:**
1. **Default Port Check:** Try connecting to `http://localhost:11434` first
2. **Failure Handling:** Show user dialog: "Ollama not detected. Running on different port or need installation?"
3. **Options Provided:**
   - Link to Ollama installation guide
   - Custom port configuration field
   - "Test Connection" button for validation
4. **Settings Integration:** Store Ollama configuration in preferences table

**Model Management:**
- **Model Discovery:** Retrieve available models from user's Ollama instance via `/api/tags`
- **User Selection:** Settings page displays available models for user choice
- **No Default Selection:** User must explicitly choose models for each processing mode
- **Model Validation:** Verify selected models exist before processing entries
- **Future Enhancement:** Model performance recommendations based on testing

**API Integration:**
```python
# Ollama service class structure
class OllamaService:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
    
    async def test_connection(self) -> bool:
        # Test if Ollama is running and responsive
    
    async def list_models(self) -> List[str]:
        # Get available models from /api/tags
    
    async def process_text(self, text: str, mode: str, model: str):
        # Process text with specified model and mode
```

### Pattern Detection Implementation

**Similarity Thresholds & Logic:**
- **Primary Similarity Threshold:** 0.7 (cosine similarity) for pattern grouping
- **Mood Pattern Threshold:** 0.75+ (higher threshold for emotional consistency)
- **Topic Pattern Threshold:** 0.7+ (standard threshold for content similarity)
- **Minimum Pattern Size:** 3+ entries with similar themes to constitute a valid pattern
- **Entry Requirement:** Hard-coded minimum of 30 entries before pattern detection unlocks

**Pattern Detection Algorithm:**
```python
# Pattern detection workflow
1. Generate embeddings for all entries (if not already present)
2. Cluster entries using cosine similarity thresholds
3. Identify clusters with 3+ entries as potential patterns
4. Classify patterns by type:
   - Mood patterns: Based on emotion-related embeddings
   - Topic patterns: Based on content embeddings  
   - Temporal patterns: Same topics within time windows
5. Calculate confidence scores based on cluster coherence
6. Store validated patterns in patterns table
```

**Pattern Regeneration Strategy:**
- **Triggers:** Weekly intervals OR every 10 new entries (whichever comes first)
- **Incremental Updates:** Only analyze new entries since last pattern detection
- **Pattern Evolution:** Update existing patterns with new matching entries
- **Confidence Scoring:** Patterns with confidence < 0.6 are hidden from UI

### Auto-Save & Draft Management

**Draft Auto-Save Implementation:**
- **Save Frequency:** Every 30 seconds while user is typing
- **STT Integration:** Save immediately after each transcription completion
- **Storage:** Temporary storage in `drafts` table with timestamp
- **Recovery UI:** Show "Resume Draft" option on New Entry page if draft exists
- **Cleanup:** Clear draft after successful entry creation

**Draft Recovery Workflow:**
```javascript
// Frontend draft recovery logic
1. Check for existing drafts on New Entry page load
2. Show notification: "You have an unsaved draft from [timestamp]"
3. Options: "Resume Draft" | "Start Fresh" | "View Draft"
4. Resume loads content into textarea with cursor at end
5. Auto-save continues with existing draft ID
```

### Error Handling & Retry Logic

**Partial Entry Processing:**
- **Entry States:** `'draft'` → `'transcribed'` → `'processed'` → `'error'`
- **Error Storage:** Store entries with `status: 'transcribed'` when Ollama processing fails
- **Retry UI:** Show error toast with "Retry Processing" button
- **Retry Logic:** Re-send original text to Ollama API with selected models
- **Success Flow:** Update status to `'processed'` and display all three versions

**Error Message Differentiation:**
```python
# Specific error messages for better UX
"Ollama connection failed - Check if Ollama is running"
"Model 'llama2' not found - Please select a different model in settings"  
"Processing timeout - Large entries may take longer, try again"
"Invalid model response - The selected model may not support this task"
```

**Graceful Degradation:**
- **STT Independence:** Voice transcription works even when Ollama is unavailable
- **Raw Mode Fallback:** Always save raw transcription, enhanced/structured optional
- **Offline Capability:** Core journaling functions available without AI processing
- **Clear Status:** UI clearly indicates which features are available/unavailable

### Resource Management & Performance

**Memory Management:**
- **STT Buffers:** Cleanup audio buffers immediately after transcription
- **Whisper Model:** Lazy-loaded on first use, cached until app shutdown
- **Embedding Cache:** LRU cache for frequently accessed embeddings
- **Model Cleanup:** Proper model disposal on app termination

**Performance Optimizations:**
- **Lazy Loading:** Load Whisper model only when first recording is initiated  
- **Background Processing:** Ollama requests processed asynchronously
- **UI Responsiveness:** Non-blocking operations with progress indicators
- **Database Indexing:** Proper indexes on timestamp, embeddings, and status columns

### Security & Privacy Considerations

**Local-First Security:**
- **No Encryption Required:** All data stays on user's machine
- **Temporary File Cleanup:** Audio buffers cleared after processing
- **No External Calls:** Only local Ollama API communication
- **Data Isolation:** Each user's data completely separate and local

**Privacy Guarantees:**
- **No Cloud Processing:** All AI processing via local Ollama
- **No Telemetry:** No usage data or analytics collection
- **User Control:** Complete ownership of journal data and AI models
- **Transparent Processing:** Open source code for full auditability

## STT Implementation Reference

### Audio Processing Pipeline (From Existing STT Implementation)

**Core Audio Capture Setup:**
```python
# Dynamic sample rate detection
device_info = sd.query_devices(None, 'input')  # None for default device
input_samplerate = int(device_info['default_samplerate'])

# Audio stream setup
stream = sd.InputStream(callback=callback, samplerate=input_samplerate, channels=1)
stream.start()

def callback(indata, frames, time, status):
    if is_recording:
        recording_data.append(indata.copy())
```

**Audio Processing & Whisper Integration:**
```python
# Convert recorded audio to numpy array
audio_data = np.concatenate(recording_data, axis=0)

# Save to in-memory WAV file
byte_io = io.BytesIO()
wav.write(byte_io, input_samplerate, audio_data)
byte_io.seek(0)

# Read back using soundfile for Whisper compatibility
audio_np, current_samplerate = sf.read(byte_io)
audio_np = audio_np.astype(np.float32)

# Resample to 16000 Hz if necessary (Whisper requirement)
if current_samplerate != 16000:
    audio_np = resample_poly(audio_np, 16000, current_samplerate)

# Whisper transcription
model = whisper.load_model(MODEL_NAME)  # Lazy loaded
result = model.transcribe(audio_np, fp16=False)
transcribed_text = result["text"]
```

**Hotkey Management System:**
```python
# Configuration-driven hotkey setup
HOTKEY = config.get("hotkey", "ctrl+shift+space")

# Hotkey registration
main_hotkey_handle = keyboard.add_hotkey(HOTKEY, start_recording, suppress=True)

# Press-and-hold detection
def monitor_hotkey_release():
    global is_hotkey_held
    while is_hotkey_held:
        if not keyboard.is_pressed(HOTKEY):
            stop_recording_and_transcribe()
            break
        time.sleep(0.05)  # Check every 50ms

# Hotkey reconfiguration
def save_new_hotkey():
    global HOTKEY, captured_hotkey_string
    HOTKEY = captured_hotkey_string
    # Clear all existing hotkeys and re-register
    keyboard.clear_all_hotkeys()
    register_main_hotkeys()
```

**Recording State Management:**
```python
# Recording states and flags
is_recording = False
recording_data = []
is_hotkey_held = False

def start_recording():
    global is_recording, recording_data, is_hotkey_held
    if not is_recording:
        is_recording = True
        is_hotkey_held = True
        recording_data = []
        # Start monitoring thread for release detection
        threading.Thread(target=monitor_hotkey_release, daemon=True).start()

def stop_recording_and_transcribe():
    global is_recording, is_hotkey_held
    if is_recording:
        is_recording = False
        is_hotkey_held = False
        # Process audio_data for transcription
```

**Configuration Management:**
```python
# Config loading with resource path handling
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller support
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_config():
    config_path = resource_path("config.json")
    with open(config_path, "r") as f:
        return json.load(f)

def save_config(new_config):
    with open(resource_path("config.json"), "w") as f:
        json.dump(new_config, f, indent=2)
```

**Required Dependencies:**
```python
# Essential imports for STT functionality
import sounddevice as sd
import whisper
import numpy as np
import scipy.io.wavfile as wav
import io
import soundfile as sf
from scipy.signal import resample_poly
import keyboard
import threading
import time
import json
```

### Visual Feedback System (Popup Integration)

**Tkinter Popup for Recording States:**
```python
# State-based popup messages
def check_popup_queue():
    command = popup_queue.get_nowait()
    if command == "show":
        popup_root.deiconify()
        popup_label.config(text="Recording...")
    elif command == "hide":
        popup_root.withdraw()
    elif command == "processing":
        popup_root.deiconify()
        popup_label.config(text="Processing...")
    elif command.startswith("text:"):
        custom_text = command[5:]
        popup_label.config(text=custom_text)

# Pulsing animation for recording feedback
def pulse_text_color():
    # Animated color pulsing based on recording state
    # Recording: Cyan (#64dddd), Processing: Orange (#ff8c00)
```

**Thread-Safe Communication:**
```python
# Queue-based communication between threads
popup_queue = queue.Queue()
popup_queue.put("show")      # Show recording popup
popup_queue.put("processing") # Show processing state
popup_queue.put("hide")      # Hide popup
```

### Integration Adaptations for DearDiary

**Key Modifications Needed:**
1. **Replace `keyboard.write()`** with WebSocket communication to React frontend
2. **Adapt popup system** to WebSocket state messages instead of Tkinter
3. **Integrate config management** with SQLite preferences table
4. **Add multi-paragraph handling** for accumulated text approach
5. **Remove AI processing parts** and focus on core STT functionality

**FastAPI Background Service Structure:**
```python
# Adapted service class for DearDiary
class STTBackgroundService:
    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager
        self.is_recording = False
        self.recording_data = []
        self.model = None  # Lazy loaded
        self.stream = None
        self.current_hotkey = "f8"
    
    async def start_recording(self):
        # Adapted from original start_recording()
        await self.websocket_manager.send_message({
            "type": "state", 
            "state": "recording",
            "message": "Recording... Release F8 to stop"
        })
    
    async def process_transcription(self):
        # Adapted transcription processing
        await self.websocket_manager.send_message({
            "type": "transcription",
            "text": transcribed_text,
            "append": True
        })
```

This comprehensive implementation specification ensures DearDiary maintains its privacy-first principles while delivering a robust, user-friendly journaling experience with sophisticated AI capabilities.
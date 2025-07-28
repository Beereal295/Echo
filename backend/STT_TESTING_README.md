# Echo STT Service Testing Guide

This guide explains how to test the Speech-to-Text (STT) service with dynamic microphone resampling functionality.

## Prerequisites

1. **Activate Virtual Environment**:
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

2. **Install Dependencies** (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

3. **Check Microphone**: Ensure your microphone is working and set as the default input device.

## Test Scripts Overview

### 1. Basic API Test (`test_stt_basic.py`)
Tests all STT API endpoints without requiring user interaction.

**Features Tested**:
- ✅ Health check endpoints
- ✅ STT service status and configuration
- ✅ Audio device detection
- ✅ Dynamic sample rate detection and resampling info
- ✅ Whisper model management
- ✅ Complete recording workflow (simulated)

**Run Command**:
```bash
python test_stt_basic.py
```

### 2. Interactive Hotkey Test (`test_stt_with_hotkey.py`)
Full interactive testing with F8 hotkey functionality.

**Features Tested**:
- ✅ All basic API functionality
- ✅ F8 hotkey press-and-hold recording
- ✅ Real-time audio capture and transcription
- ✅ Dynamic resampling (native rate → 16kHz for Whisper)
- ✅ Interactive user experience

**Run Command**:
```bash
python test_stt_with_hotkey.py
```

## Testing Workflow

### Step 1: Run Basic Tests
```bash
python test_stt_basic.py
```

**Expected Output**:
- Service initialization ✅
- Audio device detection ✅
- Sample rate information showing native vs target rates
- Whisper model loading status
- API endpoints responding correctly

### Step 2: Run Interactive Hotkey Tests
```bash
python test_stt_with_hotkey.py
```

**Test Options**:
1. **Hotkey Testing**: Press and hold F8 to record, release to stop
2. **Manual Recording**: 3-second automated recording test
3. **Both**: Run manual test then switch to hotkey mode

### Step 3: Test the Dynamic Resampling
The tests will show:
- **Native Sample Rate**: Your microphone's default rate (usually 44.1kHz or 48kHz)
- **Target Sample Rate**: 16kHz (Whisper requirement)
- **Resampling Status**: Whether resampling is needed
- **Resampling Method**: librosa with scipy fallback

## Key Features Being Tested

### 🎙️ Dynamic Microphone Resampling
- Automatically detects your microphone's native sample rate
- Captures audio at native quality (44.1kHz/48kHz)
- Resamples to 16kHz before feeding to Whisper
- Uses high-quality librosa resampling with scipy fallback

### ⌨️ F8 Hotkey Functionality
- Press and hold F8 to start recording
- Release F8 to stop and process transcription
- Visual feedback in console
- ESC key to exit

### 🤖 Whisper Integration
- Lazy model loading (loads only when needed)
- Configurable models (tiny, base, small, medium, large)
- Automatic language detection
- Confidence scoring

## Troubleshooting

### Common Issues:

1. **ModuleNotFoundError**: 
   ```bash
   pip install -r requirements.txt
   ```

2. **No Audio Devices Found**:
   - Check microphone connection
   - Verify default input device in system settings

3. **Sample Rate Issues**:
   - The system auto-detects and handles different sample rates
   - Check console output for sample rate information

4. **Hotkey Not Working**:
   - Ensure the application has focus
   - Try running as administrator (Windows)
   - Check that F8 is not bound to other applications

5. **Whisper Model Loading Slow**:
   - First run downloads models (can take time)
   - Subsequent runs use cached models
   - Start with 'tiny' model for faster testing

### Debug Information:

The tests provide detailed debug output:
- Audio device enumeration
- Sample rate detection and resampling info
- Recording state transitions
- Transcription results with confidence scores
- Error messages with specific failure points

## Expected Test Results

### Successful Basic Test:
```
🎙️ Echo STT Service Basic Tester
========================================
⚙️  Setting up test environment...
[OK] Test environment initialized

🔍 Testing Health Check
-------------------------
[OK] Health check passed
     Status: healthy
     Service: Echo Journal

🧪 Testing STT API Endpoints
------------------------------
[OK] Service Status
[OK] Audio Devices
     Total Audio Devices: 2
[OK] Sample Rate Info
     Native Sample Rate: 48000Hz
     Target Sample Rate: 16000Hz
     Resampling Needed: Yes
[OK] Available Models
[OK] Service Test
     Service Ready: ✅
```

### Successful Hotkey Test:
```
🎮 INTERACTIVE MODE - Ready for F8 hotkey testing!
Press F8 to record, ESC to exit...

🔴 F8 PRESSED - Starting recording...
[OK] Recording started: Hold to record, release to stop

⏹️  F8 RELEASED - Stopping recording (Duration: 2.3s)
[OK] Recording stopped: Recording stopped, transcription started

📝 Getting transcription...

✅ TRANSCRIPTION RESULT:
   Text: 'Hello, this is a test of the speech to text system.'
   Language: english
   Confidence: 0.92
   Segments: 1
```

## Next Steps

After successful testing, the STT service is ready for integration with:
- Task 2.2: Hotkey Management System
- Task 2.3: WebSocket Communication
- Frontend voice recording interfaces

## Support

If you encounter issues:
1. Check the detailed console output for specific error messages
2. Verify all prerequisites are met
3. Ensure microphone permissions are granted
4. Test with different Whisper models if needed
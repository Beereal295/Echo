#!/usr/bin/env python3
"""
Echo STT Service Test Script with F8 Hotkey
Tests the complete STT pipeline with hotkey integration and dynamic resampling
"""

import asyncio
import sys
import time
import json
import threading
from typing import Optional
import httpx
from httpx import ASGITransport
import pynput
from pynput import keyboard

# Add app directory to path for imports
sys.path.append('./app')

from app.main import app
from app.services.stt import get_stt_service
from app.core.config import settings


class STTTester:
    """Comprehensive STT service tester with hotkey support"""
    
    def __init__(self):
        self.client = None
        self.stt_service = None
        self.hotkey_listener = None
        self.is_recording = False
        self.test_results = {}
        self.recording_start_time = None
        
        # Hotkey configuration
        self.hotkey = keyboard.Key.f8  # F8 key
        self.hotkey_pressed = False
        
        print("🎙️ Echo STT Service Tester with F8 Hotkey")
        print("=" * 50)
    
    async def setup(self):
        """Initialize the test environment"""
        print("⚙️  Setting up test environment...")
        
        try:
            # Initialize HTTP client
            self.client = httpx.AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            )
            
            # Initialize STT service
            self.stt_service = await get_stt_service()
            
            # Hardcode language to English for testing
            self.stt_service.whisper_service.language = "english"
            
            # Setup hotkey listener
            self._setup_hotkey_listener()
            
            print("[OK] Test environment initialized")
            return True
            
        except Exception as e:
            print(f"[ERROR] Setup failed: {e}")
            return False
    
    def _setup_hotkey_listener(self):
        """Setup F8 hotkey listener"""
        try:
            def on_press(key):
                if key == self.hotkey and not self.hotkey_pressed:
                    self.hotkey_pressed = True
                    threading.Thread(target=self._sync_start_recording, daemon=True).start()
            
            def on_release(key):
                if key == self.hotkey and self.hotkey_pressed:
                    self.hotkey_pressed = False
                    threading.Thread(target=self._sync_stop_recording, daemon=True).start()
                elif key == keyboard.Key.esc:
                    print("\n👋 ESC pressed - exiting...")
                    return False
            
            self.hotkey_listener = keyboard.Listener(
                on_press=on_press,
                on_release=on_release
            )
            self.hotkey_listener.start()
            
            print(f"[OK] F8 hotkey listener started")
            
        except Exception as e:
            print(f"[ERROR] Hotkey setup failed: {e}")
    
    def _sync_start_recording(self):
        """Sync wrapper for start recording"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._start_recording())
        finally:
            loop.close()
    
    def _sync_stop_recording(self):
        """Sync wrapper for stop recording"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._stop_recording())
        finally:
            loop.close()
    
    async def _start_recording(self):
        """Start recording when F8 is pressed"""
        if self.is_recording:
            return
        
        try:
            print("\n🔴 F8 PRESSED - Starting recording...")
            self.recording_start_time = time.time()
            
            response = await self.client.post("/api/v1/stt/start")
            if response.status_code == 200:
                self.is_recording = True
                result = response.json()
                print(f"[OK] Recording started: {result['data']['message']}")
            else:
                print(f"[ERROR] Failed to start recording: {response.text}")
                
        except Exception as e:
            print(f"[ERROR] Start recording failed: {e}")
    
    async def _stop_recording(self):
        """Stop recording when F8 is released"""
        if not self.is_recording:
            return
        
        try:
            recording_duration = time.time() - self.recording_start_time if self.recording_start_time else 0
            print(f"\n⏹️  F8 RELEASED - Stopping recording (Duration: {recording_duration:.1f}s)")
            
            response = await self.client.post("/api/v1/stt/stop")
            if response.status_code == 200:
                self.is_recording = False
                result = response.json()
                print(f"[OK] Recording stopped: {result['data']['message']}")
                
                # Wait a moment then get transcription
                await asyncio.sleep(2)
                await self._get_transcription()
                
            else:
                print(f"[ERROR] Failed to stop recording: {response.text}")
                
        except Exception as e:
            print(f"[ERROR] Stop recording failed: {e}")
    
    async def _get_transcription(self):
        """Get the transcription result"""
        try:
            print("📝 Getting transcription...")
            
            response = await self.client.get("/api/v1/stt/transcription")
            if response.status_code == 200:
                result = response.json()
                
                if result['data']:
                    transcription = result['data']
                    print("\n✅ TRANSCRIPTION RESULT:")
                    print(f"   Text: '{transcription['text']}'")
                    print(f"   Language: {transcription['language']}")
                    print(f"   Confidence: {transcription['confidence']:.2f}")
                    print(f"   Segments: {len(transcription['segments'])}")
                else:
                    print("[INFO] No transcription available yet")
            else:
                print(f"[ERROR] Failed to get transcription: {response.text}")
                
        except Exception as e:
            print(f"[ERROR] Get transcription failed: {e}")
    
    async def run_basic_tests(self):
        """Run basic API tests"""
        print("\n🧪 Running Basic API Tests")
        print("-" * 30)
        
        tests = [
            ("STT Service Status", "/api/v1/stt/status"),
            ("Audio Devices", "/api/v1/stt/devices"),
            ("Sample Rate Info", "/api/v1/stt/sample-rates"),
            ("Available Models", "/api/v1/stt/models"),
            ("Service Test", "/api/v1/stt/test")
        ]
        
        for test_name, endpoint in tests:
            try:
                if "test" in endpoint:
                    response = await self.client.post(endpoint)
                else:
                    response = await self.client.get(endpoint)
                if response.status_code == 200:
                    result = response.json()
                    print(f"[OK] {test_name}")
                    
                    # Show key information for each test
                    if "sample-rates" in endpoint:
                        data = result['data']
                        print(f"     Native: {data['native_sample_rate']}Hz → Target: {data['target_sample_rate']}Hz")
                        print(f"     Resampling: {'Yes' if data['resampling_needed'] else 'No'}")
                    
                    elif "devices" in endpoint:
                        devices = result['data']['devices']
                        print(f"     Found {len(devices)} audio devices")
                        for i, device in enumerate(devices[:3]):  # Show first 3
                            print(f"     - {device['name']} ({device['sample_rate']}Hz)")
                    
                    elif "models" in endpoint:
                        models = result['data']
                        print(f"     Current: {models['current_model']['model_name']}")
                        print(f"     Available: {len(models['available_models'])} models")
                    
                    elif "test" in endpoint:
                        data = result['data']
                        print(f"     Service Ready: {data['service_ready']}")
                        print(f"     Audio Capture: {data['audio_capture']}")
                        sample_info = data.get('sample_rate_info', {})
                        if sample_info:
                            print(f"     Resampling: {'Yes' if sample_info.get('resampling_needed') else 'No'}")
                    
                else:
                    print(f"[ERROR] {test_name}: {response.status_code}")
                    
            except Exception as e:
                print(f"[ERROR] {test_name}: {e}")
    
    async def run_manual_recording_test(self):
        """Run a manual recording test via API"""
        print("\n🎯 Manual Recording Test")
        print("-" * 25)
        
        try:
            # Start recording
            print("Starting 3-second recording...")
            response = await self.client.post("/api/v1/stt/start")
            if response.status_code != 200:
                print(f"[ERROR] Failed to start: {response.text}")
                return
            
            print("[OK] Recording started - speak now!")
            await asyncio.sleep(3)  # Record for 3 seconds
            
            # Stop recording
            response = await self.client.post("/api/v1/stt/stop")
            if response.status_code != 200:
                print(f"[ERROR] Failed to stop: {response.text}")
                return
            
            print("[OK] Recording stopped - processing...")
            await asyncio.sleep(2)  # Wait for processing
            
            # Get transcription
            await self._get_transcription()
            
        except Exception as e:
            print(f"[ERROR] Manual test failed: {e}")
    
    def print_instructions(self):
        """Print user instructions"""
        print("\n📋 TEST INSTRUCTIONS")
        print("=" * 50)
        print("🎯 HOTKEY TESTING:")
        print("   • Press and HOLD F8 to start recording")
        print("   • Release F8 to stop recording and get transcription")
        print("   • Press ESC to exit the test")
        print()
        print("💡 TIPS:")
        print("   • Speak clearly while holding F8")
        print("   • Wait for transcription results after releasing F8")
        print("   • Check console for detailed status messages")
        print()
        print("🔊 AUDIO SETUP:")
        print("   • Ensure your microphone is working")
        print("   • Check that your default audio device is correct")
        print("   • Speak in a quiet environment for best results")
        print()
    
    async def interactive_mode(self):
        """Run interactive testing mode"""
        print("\n🎮 INTERACTIVE MODE - Ready for F8 hotkey testing!")
        print("Press F8 to record, ESC to exit...")
        
        try:
            # Keep the event loop running
            while self.hotkey_listener.running:
                await asyncio.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n👋 Interrupted by user")
        finally:
            if self.hotkey_listener:
                self.hotkey_listener.stop()
    
    async def cleanup(self):
        """Clean up resources"""
        print("\n🧹 Cleaning up...")
        
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        
        if self.client:
            await self.client.aclose()
        
        if self.stt_service:
            self.stt_service.cleanup()
        
        print("[OK] Cleanup completed")


async def main():
    """Main test runner"""
    tester = STTTester()
    
    try:
        # Setup
        if not await tester.setup():
            return 1
        
        # Run basic tests first
        await tester.run_basic_tests()
        
        # Ask user what they want to test
        print("\n🚀 TEST OPTIONS")
        print("=" * 20)
        print("1. Hotkey Testing (Press F8 to record)")
        print("2. Manual Recording Test (3-second recording)")
        print("3. Both tests")
        print("4. Exit")
        
        try:
            choice = input("\nSelect option (1-4): ").strip()
        except KeyboardInterrupt:
            print("\n👋 Interrupted by user")
            return 0
        
        if choice == "1":
            tester.print_instructions()
            await tester.interactive_mode()
        elif choice == "2":
            await tester.run_manual_recording_test()
        elif choice == "3":
            await tester.run_manual_recording_test()
            tester.print_instructions()
            await tester.interactive_mode()
        elif choice == "4":
            print("👋 Exiting...")
        else:
            print("❌ Invalid choice")
        
        return 0
        
    except Exception as e:
        print(f"[FATAL ERROR] {e}")
        return 1
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    print("🎤 Echo STT Service Test with F8 Hotkey")
    print("Starting test environment...")
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"[FATAL] Test runner failed: {e}")
        sys.exit(1)
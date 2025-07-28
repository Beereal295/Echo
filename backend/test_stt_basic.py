#!/usr/bin/env python3
"""
Echo STT Service Basic Test Script
Tests the STT API endpoints and dynamic resampling functionality
"""

import asyncio
import sys
import time
import json
import httpx
from httpx import ASGITransport

# Add app directory to path for imports
sys.path.append('./app')

from app.main import app


class BasicSTTTester:
    """Basic STT service API tester"""
    
    def __init__(self):
        self.client = None
        print("🎙️ Echo STT Service Basic Tester")
        print("=" * 40)
    
    async def setup(self):
        """Initialize the test environment"""
        print("⚙️  Setting up test environment...")
        
        try:
            # Initialize HTTP client
            self.client = httpx.AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            )
            
            print("[OK] Test environment initialized")
            return True
            
        except Exception as e:
            print(f"[ERROR] Setup failed: {e}")
            return False
    
    async def test_health_check(self):
        """Test basic health endpoint"""
        print("\n🔍 Testing Health Check")
        print("-" * 25)
        
        try:
            response = await self.client.get("/health")
            if response.status_code == 200:
                result = response.json()
                print(f"[OK] Health check passed")
                print(f"     Status: {result['status']}")
                print(f"     Service: {result['service']}")
            else:
                print(f"[ERROR] Health check failed: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] Health check error: {e}")
    
    async def test_stt_endpoints(self):
        """Test all STT endpoints"""
        print("\n🧪 Testing STT API Endpoints")
        print("-" * 30)
        
        endpoints = [
            ("Service Status", "GET", "/api/v1/stt/status"),
            ("Audio Devices", "GET", "/api/v1/stt/devices"),
            ("Sample Rate Info", "GET", "/api/v1/stt/sample-rates"),
            ("Available Models", "GET", "/api/v1/stt/models"),
            ("Service Test", "GET", "/api/v1/stt/test")
        ]
        
        for test_name, method, endpoint in endpoints:
            try:
                if method == "GET":
                    response = await self.client.get(endpoint)
                else:
                    response = await self.client.post(endpoint)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"[OK] {test_name}")
                    
                    # Show detailed information for key endpoints
                    if "sample-rates" in endpoint:
                        data = result['data']
                        print(f"     Native Sample Rate: {data['native_sample_rate']}Hz")
                        print(f"     Target Sample Rate: {data['target_sample_rate']}Hz")
                        print(f"     Resampling Needed: {'Yes' if data['resampling_needed'] else 'No'}")
                        if data['resampling_needed']:
                            print(f"     Resampling Ratio: {data['resampling_ratio']:.3f}")
                        print(f"     Method: {data.get('resampling_method', 'N/A')}")
                    
                    elif "devices" in endpoint:
                        devices = result['data']['devices']
                        print(f"     Total Audio Devices: {len(devices)}")
                        print("     Available Devices:")
                        for i, device in enumerate(devices):
                            print(f"       {i+1}. {device['name']}")
                            print(f"          Channels: {device['channels']}, Rate: {device['sample_rate']}Hz")
                    
                    elif "models" in endpoint:
                        data = result['data']
                        current = data['current_model']
                        print(f"     Current Model: {current['model_name']}")
                        print(f"     Device: {current['device']}")
                        print(f"     Language: {current['language'] or 'Auto-detect'}")
                        print(f"     Loaded: {'Yes' if current['loaded'] else 'No'}")
                        print(f"     Available Models: {', '.join(data['available_models'][:5])}...")
                    
                    elif "status" in endpoint:
                        data = result['data']
                        print(f"     Current State: {data['state']}")
                        print(f"     State Message: {data['state_message']}")
                        if 'sample_rate_info' in data:
                            sri = data['sample_rate_info']
                            print(f"     Audio Setup: {sri['native_sample_rate']}Hz → {sri['target_sample_rate']}Hz")
                    
                    elif "test" in endpoint:
                        data = result['data']
                        print(f"     Service Ready: {'✅' if data['service_ready'] else '❌'}")
                        print(f"     Audio Capture: {'✅' if data['audio_capture'] else '❌'}")
                        print(f"     Audio Devices: {data['audio_devices_count']}")
                        print(f"     Current State: {data['current_state']}")
                        
                        if 'sample_rate_info' in data:
                            sri = data['sample_rate_info']
                            print(f"     Resampling: {'Enabled' if sri['resampling_needed'] else 'Not needed'}")
                    
                else:
                    print(f"[ERROR] {test_name}: HTTP {response.status_code}")
                    print(f"         {response.text}")
                    
            except Exception as e:
                print(f"[ERROR] {test_name}: {e}")
    
    async def test_recording_workflow(self):
        """Test the complete recording workflow"""
        print("\n🎯 Testing Recording Workflow")
        print("-" * 30)
        
        try:
            # Test start recording
            print("1. Starting recording...")
            response = await self.client.post("/api/v1/stt/start")
            if response.status_code == 200:
                result = response.json()
                print(f"[OK] Recording started: {result['message']}")
                print(f"     State: {result['data']['state']}")
            else:
                print(f"[ERROR] Failed to start recording: {response.status_code}")
                print(f"         {response.text}")
                return
            
            # Simulate recording time
            print("2. Simulating 2-second recording...")
            await asyncio.sleep(2)
            
            # Test stop recording
            print("3. Stopping recording...")
            response = await self.client.post("/api/v1/stt/stop")
            if response.status_code == 200:
                result = response.json()
                print(f"[OK] Recording stopped: {result['message']}")
                print(f"     State: {result['data']['state']}")
            else:
                print(f"[ERROR] Failed to stop recording: {response.status_code}")
                print(f"         {response.text}")
                return
            
            # Wait for processing
            print("4. Waiting for processing...")
            await asyncio.sleep(3)
            
            # Test get transcription
            print("5. Getting transcription...")
            response = await self.client.get("/api/v1/stt/transcription")
            if response.status_code == 200:
                result = response.json()
                if result['data']:
                    transcription = result['data']
                    print(f"[OK] Transcription received:")
                    print(f"     Text: '{transcription['text']}'")
                    print(f"     Language: {transcription['language']}")
                    print(f"     Confidence: {transcription['confidence']:.3f}")
                    print(f"     Segments: {len(transcription['segments'])}")
                else:
                    print("[INFO] No transcription data available (no audio captured)")
            else:
                print(f"[ERROR] Failed to get transcription: {response.status_code}")
            
            # Test cancel (should reset state)
            print("6. Testing cancel functionality...")
            response = await self.client.post("/api/v1/stt/cancel")
            if response.status_code == 200:
                result = response.json()
                print(f"[OK] Cancel test: {result['message']}")
                print(f"     State: {result['data']['state']}")
            else:
                print(f"[ERROR] Cancel test failed: {response.status_code}")
            
        except Exception as e:
            print(f"[ERROR] Recording workflow test failed: {e}")
    
    async def test_model_management(self):
        """Test Whisper model management"""
        print("\n🤖 Testing Model Management")
        print("-" * 28)
        
        try:
            # Get available models
            response = await self.client.get("/api/v1/stt/models")
            if response.status_code != 200:
                print("[ERROR] Could not get available models")
                return
            
            models_data = response.json()['data']
            available_models = models_data['available_models']
            current_model = models_data['current_model']['model_name']
            
            print(f"Current model: {current_model}")
            print(f"Available models: {', '.join(available_models)}")
            
            # Test changing to a different model (if available)
            if len(available_models) > 1:
                test_model = None
                for model in ['tiny', 'base', 'small']:
                    if model in available_models and model != current_model:
                        test_model = model
                        break
                
                if test_model:
                    print(f"\nTesting model change to: {test_model}")
                    
                    # Note: We won't actually change the model in testing to avoid
                    # long loading times, but we'll test the endpoint validation
                    print(f"[INFO] Model change endpoint available (not testing actual change)")
                    print(f"       Would change from {current_model} to {test_model}")
                else:
                    print("[INFO] No alternative models available for testing")
            else:
                print("[INFO] Only one model available, skipping change test")
            
        except Exception as e:
            print(f"[ERROR] Model management test failed: {e}")
    
    async def cleanup(self):
        """Clean up resources"""
        if self.client:
            await self.client.aclose()


async def main():
    """Main test runner"""
    tester = BasicSTTTester()
    
    try:
        # Setup
        if not await tester.setup():
            return 1
        
        # Run all tests
        await tester.test_health_check()
        await tester.test_stt_endpoints()
        await tester.test_recording_workflow()
        await tester.test_model_management()
        
        print("\n✅ All basic tests completed!")
        print("\n💡 For interactive testing with F8 hotkey, run:")
        print("   python test_stt_with_hotkey.py")
        
        return 0
        
    except Exception as e:
        print(f"[FATAL ERROR] {e}")
        return 1
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    print("🎤 Echo STT Service Basic Test")
    print("Testing API endpoints and functionality...")
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"[FATAL] Test runner failed: {e}")
        sys.exit(1)
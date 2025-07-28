#!/usr/bin/env python3
"""
Simple test script for Hotkey API endpoints
Tests the hotkey management API without requiring global hotkey registration
"""

import asyncio
import sys
import httpx
from httpx import ASGITransport

# Add app directory to path for imports
sys.path.append('./app')

from app.main import app


async def test_hotkey_api():
    """Test hotkey API endpoints"""
    
    print("⌨️ Simple Hotkey API Test")
    print("=" * 30)
    
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        
        # Test basic endpoints
        tests = [
            ("GET", "/api/v1/hotkey/current", None, "Current Hotkey"),
            ("GET", "/api/v1/hotkey/suggestions", None, "Hotkey Suggestions"),
            ("POST", "/api/v1/hotkey/validate", {"hotkey": "f8"}, "Validate F8"),
            ("POST", "/api/v1/hotkey/validate", {"hotkey": "ctrl+alt+f8"}, "Validate Ctrl+Alt+F8"),
            ("POST", "/api/v1/hotkey/validate", {"hotkey": "invalid"}, "Validate Invalid"),
            ("GET", "/api/v1/hotkey/status", None, "Service Status"),
        ]
        
        for method, endpoint, json_data, test_name in tests:
            try:
                
                if method == "GET":
                    response = await client.get(endpoint)
                else:
                    response = await client.post(endpoint, json=json_data)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ {test_name}")
                    
                    # Show specific info for each test
                    if "current" in endpoint:
                        data = result['data']
                        print(f"   Current: {data['hotkey']}")
                    
                    elif "suggestions" in endpoint:
                        data = result['data']
                        print(f"   Suggestions: {', '.join(data['suggestions'][:3])}...")
                    
                    elif "validate" in endpoint:
                        data = result['data']
                        status = "Valid" if data['valid'] else "Invalid"
                        hotkey = json_data['hotkey'] if json_data else "unknown"
                        print(f"   {hotkey}: {status}")
                        if data['errors']:
                            print(f"   Errors: {', '.join(data['errors'])}")
                        if data['warnings']:
                            print(f"   Warnings: {', '.join(data['warnings'])}")
                    
                    elif "status" in endpoint:
                        data = result['data']
                        print(f"   Service Running: {data['service_running']}")
                        print(f"   Current Hotkey: {data['current_hotkey']}")
                        print(f"   STT Available: {data['stt_service_available']}")
                
                else:
                    print(f"❌ {test_name}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {test_name}: {e}")
        
        # Test hotkey change
        print("\n🔄 Testing Hotkey Change")
        try:
            # Change to F9
            response = await client.post("/api/v1/hotkey/change", json={"hotkey": "f9"})
            if response.status_code == 200:
                print("✅ Changed to F9")
                
                # Change back to F8
                response = await client.post("/api/v1/hotkey/change", json={"hotkey": "f8"}) 
                if response.status_code == 200:
                    print("✅ Changed back to F8")
                else:
                    print(f"❌ Failed to change back: {response.text}")
            else:
                print(f"❌ Failed to change: {response.text}")
        except Exception as e:
            print(f"❌ Hotkey change test: {e}")
        
        print("\n✅ API tests completed!")
        print("\n💡 Note: Global hotkey functionality requires:")
        print("   • Running outside test environment")
        print("   • Proper system permissions")
        print("   • Active window manager")


if __name__ == "__main__":
    try:
        asyncio.run(test_hotkey_api())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted")
    except Exception as e:
        print(f"❌ Test failed: {e}")
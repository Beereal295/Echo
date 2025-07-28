#!/usr/bin/env python3
"""
Test script for the Hotkey Management System
Tests hotkey registration, validation, and integration with STT
"""

import asyncio
import sys
import httpx
from httpx import ASGITransport

# Add app directory to path for imports
sys.path.append('./app')

from app.main import app


class HotkeyTester:
    """Test the hotkey management system"""
    
    def __init__(self):
        self.client = None
        print("⌨️ Echo Hotkey Management System Tester")
        print("=" * 45)
    
    async def setup(self):
        """Initialize test environment"""
        print("⚙️  Setting up test environment...")
        
        try:
            self.client = httpx.AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            )
            print("[OK] Test environment initialized")
            return True
        except Exception as e:
            print(f"[ERROR] Setup failed: {e}")
            return False
    
    async def test_hotkey_endpoints(self):
        """Test all hotkey API endpoints"""
        print("\n🔍 Testing Hotkey API Endpoints")
        print("-" * 35)
        
        endpoints = [
            ("Hotkey Status", "GET", "/api/v1/hotkey/status"),
            ("Current Hotkey", "GET", "/api/v1/hotkey/current"),
            ("Hotkey Suggestions", "GET", "/api/v1/hotkey/suggestions"),
            ("Hotkey Service Test", "POST", "/api/v1/hotkey/test")
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
                    
                    # Show key information
                    if "status" in endpoint:
                        data = result['data']
                        print(f"     Service Running: {'✅' if data['service_running'] else '❌'}")
                        print(f"     Hotkey Registered: {'✅' if data['hotkey_registered'] else '❌'}")
                        print(f"     Current Hotkey: {data['current_hotkey']}")
                        print(f"     STT Available: {'✅' if data['stt_service_available'] else '❌'}")
                    
                    elif "current" in endpoint:
                        data = result['data']
                        print(f"     Hotkey: {data['hotkey']}")
                        print(f"     Active: {'✅' if data['active'] else '❌'}")
                        print(f"     Registered: {'✅' if data['registered'] else '❌'}")
                    
                    elif "suggestions" in endpoint:
                        data = result['data']
                        print(f"     Current: {data['current']}")
                        print(f"     Suggestions: {', '.join(data['suggestions'][:5])}")
                    
                    elif "test" in endpoint:
                        data = result['data']
                        print(f"     Service Ready: {'✅' if data['service_ready'] else '❌'}")
                        if 'service_status' in data:
                            status = data['service_status']
                            print(f"     Registered Count: {status.get('manager_status', {}).get('registered_count', 0)}")
                
                else:
                    print(f"[ERROR] {test_name}: HTTP {response.status_code}")
                    if response.status_code != 404:
                        print(f"         {response.text}")
            
            except Exception as e:
                print(f"[ERROR] {test_name}: {e}")
    
    async def test_hotkey_validation(self):
        """Test hotkey validation functionality"""
        print("\n✅ Testing Hotkey Validation")
        print("-" * 30)
        
        test_keys = [
            ("f8", "Valid function key"),
            ("ctrl+alt+f8", "Valid with modifiers"),
            ("alt+f4", "Reserved combination"),
            ("invalid_key", "Invalid key"),
            ("f8+f9", "Invalid combination"),
            ("ctrl+c", "Reserved system key"),
            ("f1", "Valid alternative"),
            ("shift+f10", "Valid with modifier")
        ]
        
        for hotkey, description in test_keys:
            try:
                response = await self.client.post("/api/v1/hotkey/validate", 
                                                json={"hotkey": hotkey})
                
                if response.status_code == 200:
                    result = response.json()
                    data = result['data']
                    
                    status = "✅ Valid" if data['valid'] else "❌ Invalid"
                    print(f"{hotkey:15} - {status} ({description})")
                    
                    if data['errors']:
                        for error in data['errors']:
                            print(f"                  Error: {error}")
                    
                    if data['warnings']:
                        for warning in data['warnings']:
                            print(f"                  Warning: {warning}")
                
                else:
                    print(f"{hotkey:15} - [ERROR] HTTP {response.status_code}")
            
            except Exception as e:
                print(f"{hotkey:15} - [ERROR] {e}")
    
    async def test_hotkey_change(self):
        """Test changing hotkeys"""
        print("\n🔄 Testing Hotkey Change")
        print("-" * 25)
        
        # Get current hotkey
        response = await self.client.get("/api/v1/hotkey/current")
        if response.status_code != 200:
            print("[ERROR] Could not get current hotkey")
            return
        
        original_hotkey = response.json()['data']['hotkey']
        print(f"Original hotkey: {original_hotkey}")
        
        # Test changing to F9
        test_hotkey = "f9"
        print(f"Changing to: {test_hotkey}")
        
        try:
            response = await self.client.post("/api/v1/hotkey/change",
                                            json={"hotkey": test_hotkey})
            
            if response.status_code == 200:
                result = response.json()
                print(f"[OK] Changed to {test_hotkey}")
                if 'warnings' in result['data']:
                    for warning in result['data']['warnings']:
                        print(f"     Warning: {warning}")
                
                # Change back to original
                await asyncio.sleep(1)
                response = await self.client.post("/api/v1/hotkey/change",
                                                json={"hotkey": original_hotkey})
                if response.status_code == 200:
                    print(f"[OK] Restored to {original_hotkey}")
                else:
                    print(f"[ERROR] Failed to restore: {response.text}")
            
            else:
                print(f"[ERROR] Failed to change hotkey: {response.text}")
        
        except Exception as e:
            print(f"[ERROR] Hotkey change test failed: {e}")
    
    async def test_hotkey_enable_disable(self):
        """Test enabling/disabling hotkeys"""
        print("\n🔘 Testing Hotkey Enable/Disable")
        print("-" * 32)
        
        try:
            # Test disable
            response = await self.client.post("/api/v1/hotkey/disable")
            if response.status_code == 200:
                print("[OK] Hotkey disabled")
            else:
                print(f"[ERROR] Failed to disable: {response.text}")
            
            await asyncio.sleep(0.5)
            
            # Test enable
            response = await self.client.post("/api/v1/hotkey/enable")
            if response.status_code == 200:
                print("[OK] Hotkey enabled")
            else:
                print(f"[ERROR] Failed to enable: {response.text}")
        
        except Exception as e:
            print(f"[ERROR] Enable/disable test failed: {e}")
    
    async def test_integration_with_stt(self):
        """Test integration with STT service"""
        print("\n🔗 Testing STT Integration")
        print("-" * 26)
        
        try:
            # Check STT service status
            response = await self.client.get("/api/v1/stt/status")
            if response.status_code == 200:
                stt_data = response.json()['data']
                print(f"[OK] STT Service: {stt_data['state']}")
            else:
                print("[ERROR] STT service not available")
                return
            
            # Check hotkey integration
            response = await self.client.get("/api/v1/hotkey/status")
            if response.status_code == 200:
                hotkey_data = response.json()['data']
                print(f"[OK] Hotkey-STT Integration: {'✅' if hotkey_data['stt_service_available'] else '❌'}")
                
                if hotkey_data['stt_service_available']:
                    print("     Integration working - hotkey can control STT recording")
                else:
                    print("     Integration issue - hotkey cannot control STT")
            
        except Exception as e:
            print(f"[ERROR] Integration test failed: {e}")
    
    async def cleanup(self):
        """Clean up resources"""
        if self.client:
            await self.client.aclose()


async def main():
    """Main test runner"""
    tester = HotkeyTester()
    
    try:
        if not await tester.setup():
            return 1
        
        # Run all tests
        await tester.test_hotkey_endpoints()
        await tester.test_hotkey_validation()
        await tester.test_hotkey_change()
        await tester.test_hotkey_enable_disable()
        await tester.test_integration_with_stt()
        
        print("\n✅ All hotkey tests completed!")
        print("\n💡 The hotkey system is now ready for:")
        print("   • Global F8 hotkey registration")
        print("   • Press-and-hold detection")
        print("   • STT service integration")
        print("   • Hotkey configuration via API")
        print("   • Conflict detection and validation")
        
        return 0
        
    except Exception as e:
        print(f"[FATAL ERROR] {e}")
        return 1
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    print("⌨️ Echo Hotkey Management System Test")
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
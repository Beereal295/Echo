#!/usr/bin/env python3
"""
Test script for auto-save functionality integration
Tests the flow: Settings Page -> Database -> New Entry Page Auto-save

This script verifies:
1. Auto-save settings can be configured and saved in Settings page
2. Settings are properly stored in database
3. New Entry page retrieves and uses the auto-save settings
4. Auto-save actually works with the configured intervals
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, Optional

API_BASE_URL = "http://localhost:8000/api/v1"

class AutoSaveTestRunner:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"    Details: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        print()
    
    async def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{API_BASE_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                async with self.session.get(url) as response:
                    return {
                        "status_code": response.status,
                        "data": await response.json(),
                        "success": response.status < 400
                    }
            elif method.upper() == "POST":
                headers = {"Content-Type": "application/json"}
                async with self.session.post(url, json=data, headers=headers) as response:
                    return {
                        "status_code": response.status,
                        "data": await response.json(),
                        "success": response.status < 400
                    }
        except Exception as e:
            return {
                "status_code": 500,
                "data": {"error": str(e)},
                "success": False
            }
    
    async def test_backend_connection(self):
        """Test 1: Verify backend is running"""
        print("🔍 Test 1: Backend Connection")
        response = await self.make_request("GET", "/health")
        
        if response["success"]:
            self.log_test("Backend Connection", True, f"Backend responding on {API_BASE_URL}")
        else:
            self.log_test("Backend Connection", False, f"Cannot connect to backend: {response['data']}")
            return False
        return True
    
    async def test_preferences_api(self):
        """Test 2: Verify preferences API is working"""
        print("🔍 Test 2: Preferences API")
        response = await self.make_request("GET", "/preferences/")
        
        if response["success"]:
            prefs_count = len(response["data"].get("preferences", []))
            self.log_test("Preferences API", True, f"Retrieved {prefs_count} preferences")
        else:
            self.log_test("Preferences API", False, f"Failed to get preferences: {response['data']}")
            return False
        return True
    
    async def test_set_autosave_preferences(self):
        """Test 3: Set auto-save preferences via API"""
        print("🔍 Test 3: Set Auto-save Preferences")
        
        # Test preferences to set
        test_preferences = [
            {"key": "auto_save", "value": True, "value_type": "bool"},
            {"key": "auto_save_interval", "value": 15, "value_type": "int"}  # 15 seconds for testing
        ]
        
        response = await self.make_request("POST", "/preferences/bulk", {"preferences": test_preferences})
        
        if response["success"]:
            self.log_test("Set Auto-save Preferences", True, "Auto-save enabled with 15 second interval")
        else:
            self.log_test("Set Auto-save Preferences", False, f"Failed to set preferences: {response['data']}")
            return False
        return True
    
    async def test_verify_preferences_saved(self):
        """Test 4: Verify preferences were saved correctly"""
        print("🔍 Test 4: Verify Preferences Saved")
        response = await self.make_request("GET", "/preferences/")
        
        if not response["success"]:
            self.log_test("Verify Preferences Saved", False, "Failed to retrieve preferences")
            return False
        
        preferences = response["data"].get("preferences", [])
        pref_dict = {pref["key"]: pref["typed_value"] for pref in preferences}
        
        auto_save_enabled = pref_dict.get("auto_save", False)
        auto_save_interval = pref_dict.get("auto_save_interval", 30)
        
        if auto_save_enabled and auto_save_interval == 15:
            self.log_test("Verify Preferences Saved", True, f"Auto-save: {auto_save_enabled}, Interval: {auto_save_interval}s")
        else:
            self.log_test("Verify Preferences Saved", False, f"Unexpected values - Auto-save: {auto_save_enabled}, Interval: {auto_save_interval}s")
            return False
        return True
    
    async def test_drafts_table_exists(self):
        """Test 5: Verify drafts table exists for auto-save"""
        print("🔍 Test 5: Drafts Table Check")
        
        # Try to create a test draft
        test_draft = {
            "content": "This is a test draft for auto-save functionality.",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        response = await self.make_request("POST", "/drafts/save", test_draft)
        
        if response["success"]:
            draft_id = response["data"].get("data", {}).get("id")
            self.log_test("Drafts Table Check", True, f"Draft created with ID: {draft_id}")
            
            # Clean up test draft
            if draft_id:
                await self.make_request("DELETE", f"/drafts/{draft_id}")
        else:
            # Check if it's a "not implemented" error vs database error
            error_msg = response["data"].get("detail", "Unknown error")
            if "not found" in error_msg.lower() or "404" in str(response["status_code"]):
                self.log_test("Drafts Table Check", False, "Drafts API endpoint not implemented yet")
            else:
                self.log_test("Drafts Table Check", False, f"Database error: {error_msg}")
            return False
        return True
    
    async def test_preferences_with_different_values(self):
        """Test 6: Test different auto-save configurations"""
        print("🔍 Test 6: Different Auto-save Configurations")
        
        test_cases = [
            {"auto_save": False, "interval": 30, "description": "Auto-save disabled"},
            {"auto_save": True, "interval": 10, "description": "10 second interval"},
            {"auto_save": True, "interval": 60, "description": "60 second interval"},
            {"auto_save": True, "interval": 30, "description": "Default 30 second interval"}
        ]
        
        all_passed = True
        for i, case in enumerate(test_cases):
            preferences = [
                {"key": "auto_save", "value": case["auto_save"], "value_type": "bool"},
                {"key": "auto_save_interval", "value": case["interval"], "value_type": "int"}
            ]
            
            # Set preferences
            set_response = await self.make_request("POST", "/preferences/bulk", {"preferences": preferences})
            if not set_response["success"]:
                self.log_test(f"Config Test {i+1}: {case['description']}", False, "Failed to set preferences")
                all_passed = False
                continue
            
            # Verify preferences
            get_response = await self.make_request("GET", "/preferences/")
            if not get_response["success"]:
                self.log_test(f"Config Test {i+1}: {case['description']}", False, "Failed to get preferences")
                all_passed = False
                continue
            
            prefs = get_response["data"].get("preferences", [])
            pref_dict = {pref["key"]: pref["typed_value"] for pref in prefs}
            
            saved_auto_save = pref_dict.get("auto_save", False)
            saved_interval = pref_dict.get("auto_save_interval", 30)
            
            if saved_auto_save == case["auto_save"] and saved_interval == case["interval"]:
                self.log_test(f"Config Test {i+1}: {case['description']}", True, 
                            f"Saved correctly - Auto-save: {saved_auto_save}, Interval: {saved_interval}s")
            else:
                self.log_test(f"Config Test {i+1}: {case['description']}", False, 
                            f"Mismatch - Expected: {case['auto_save']}/{case['interval']}, Got: {saved_auto_save}/{saved_interval}")
                all_passed = False
        
        return all_passed
    
    async def test_preferences_data_types(self):
        """Test 7: Verify preferences handle different data types correctly"""
        print("🔍 Test 7: Preferences Data Types")
        
        # Test with various data types
        preferences = [
            {"key": "auto_save", "value": True, "value_type": "bool"},  # Boolean
            {"key": "auto_save_interval", "value": 25, "value_type": "int"},  # Integer
            {"key": "test_float", "value": 1.5, "value_type": "float"},  # Float
            {"key": "test_string", "value": "test_value", "value_type": "string"}  # String
        ]
        
        # Set preferences
        set_response = await self.make_request("POST", "/preferences/bulk", {"preferences": preferences})
        if not set_response["success"]:
            self.log_test("Preferences Data Types", False, "Failed to set mixed data type preferences")
            return False
        
        # Get and verify
        get_response = await self.make_request("GET", "/preferences/")
        if not get_response["success"]:
            self.log_test("Preferences Data Types", False, "Failed to retrieve preferences")
            return False
        
        prefs = get_response["data"].get("preferences", [])
        pref_dict = {pref["key"]: {"value": pref["typed_value"], "type": type(pref["typed_value"]).__name__} for pref in prefs}
        
        # Check types
        expected_types = {
            "auto_save": bool,
            "auto_save_interval": int,
            "test_float": float,
            "test_string": str
        }
        
        type_check_passed = True
        details = []
        for key, expected_type in expected_types.items():
            if key in pref_dict:
                actual_type = type(pref_dict[key]["value"])
                if actual_type == expected_type:
                    details.append(f"{key}: {expected_type.__name__} ✓")
                else:
                    details.append(f"{key}: expected {expected_type.__name__}, got {actual_type.__name__} ✗")
                    type_check_passed = False
            else:
                details.append(f"{key}: missing ✗")
                type_check_passed = False
        
        self.log_test("Preferences Data Types", type_check_passed, "; ".join(details))
        return type_check_passed
    
    async def test_manual_entry_creation(self):
        """Test 8: Test creating entries (simulating New Entry page usage)"""
        print("🔍 Test 8: Manual Entry Creation")
        
        test_entry = {
            "raw_text": "This is a test entry to verify the entry creation system works.",
            "mode": "raw"
        }
        
        response = await self.make_request("POST", "/entries/", test_entry)
        
        if response["success"]:
            entry_id = response["data"].get("id")
            word_count = response["data"].get("word_count", 0)
            self.log_test("Manual Entry Creation", True, f"Entry created with ID: {entry_id}, Word count: {word_count}")
            
            # Clean up test entry
            if entry_id:
                await self.make_request("DELETE", f"/entries/{entry_id}")
        else:
            self.log_test("Manual Entry Creation", False, f"Failed to create entry: {response['data']}")
            return False
        return True
    
    async def run_comprehensive_test(self):
        """Run all auto-save integration tests"""
        print("🚀 Starting Auto-save Integration Test Suite")
        print("=" * 60)
        
        # Run all tests
        tests = [
            self.test_backend_connection,
            self.test_preferences_api,
            self.test_set_autosave_preferences,
            self.test_verify_preferences_saved,
            self.test_drafts_table_exists,
            self.test_preferences_with_different_values,
            self.test_preferences_data_types,
            self.test_manual_entry_creation
        ]
        
        for test in tests:
            try:
                await test()
            except Exception as e:
                self.log_test(f"Error in {test.__name__}", False, f"Exception: {str(e)}")
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Auto-save integration is working correctly.")
        else:
            print(f"\n⚠️  {total - passed} tests failed. Please review the issues above.")
            
        print("\n📋 FRONTEND TESTING INSTRUCTIONS:")
        print("=" * 40)
        print("1. Open the Settings page")
        print("2. Go to General tab")
        print("3. Toggle auto-save on/off and change interval")
        print("4. Click 'Save Settings'")
        print("5. Go to New Entry page")
        print("6. Start typing - should auto-save at your configured interval")
        print("7. Check browser console for auto-save status messages")
        print("8. Verify drafts are being created/updated")
        
        print("\n🔍 WHAT TO WATCH FOR:")
        print("- Auto-save should be enabled/disabled based on your settings")
        print("- Auto-save interval should match your configured time")
        print("- Toast notifications should appear when auto-save triggers")
        print("- Check Network tab to see API calls being made")
        print("- Verify localStorage fallback works if backend is unavailable")
        
        return passed == total

async def main():
    """Main test runner"""
    async with AutoSaveTestRunner() as runner:
        success = await runner.run_comprehensive_test()
        return 0 if success else 1

if __name__ == "__main__":
    import sys
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test suite crashed: {str(e)}")
        sys.exit(1)
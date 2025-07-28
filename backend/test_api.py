import asyncio
import httpx
import sys
sys.path.append(".")

from app.main import app
from app.db import init_db


async def test_api_endpoints():
    """Test API endpoints with httpx"""
    print("Testing API endpoints...")
    
    # Initialize database first
    await init_db()
    print("[OK] Database initialized")
    
    # Test with httpx client
    from httpx import ASGITransport
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        
        # Test root endpoint
        print("\n1. Testing root endpoint...")
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Echo Journal API"
        print("[OK] Root endpoint working")
        
        # Test health endpoint
        print("\n2. Testing health endpoints...")
        response = await client.get("/api/v1/health/")
        assert response.status_code == 200
        print("[OK] Health endpoint working")
        
        response = await client.get("/api/v1/health/database")
        assert response.status_code == 200
        print("[OK] Database health endpoint working")
        
        # Test preferences endpoints
        print("\n3. Testing preferences endpoints...")
        response = await client.get("/api/v1/preferences/")
        assert response.status_code == 200
        prefs = response.json()
        assert "preferences" in prefs
        print(f"[OK] Found {len(prefs['preferences'])} default preferences")
        
        # Test getting specific preference
        response = await client.get("/api/v1/preferences/hotkey")
        assert response.status_code == 200
        pref = response.json()
        assert pref["key"] == "hotkey"
        original_hotkey = pref["typed_value"]  # Store original value
        print(f"[OK] Individual preference retrieval working (current value: {original_hotkey})")
        
        # Test updating preference
        test_hotkey = "F10"  # Use a different test value
        update_data = {
            "key": "hotkey",
            "value": test_hotkey,
            "value_type": "string",
            "description": "Updated hotkey for testing"
        }
        response = await client.put("/api/v1/preferences/hotkey", json=update_data)
        assert response.status_code == 200
        updated_pref = response.json()
        assert updated_pref["typed_value"] == test_hotkey
        print(f"[OK] Preference update working (updated to: {test_hotkey})")
        
        # Restore original value
        restore_data = {
            "key": "hotkey",
            "value": original_hotkey,
            "value_type": "string",
            "description": "Global hotkey for voice recording"
        }
        await client.put("/api/v1/preferences/hotkey", json=restore_data)
        print(f"[OK] Preference restored to original value: {original_hotkey}")
        
        # Test entries endpoints
        print("\n4. Testing entries endpoints...")
        
        # Test entry creation
        entry_data = {
            "raw_text": "This is a test journal entry for API testing.",
            "mode": "raw"
        }
        response = await client.post("/api/v1/entries/", json=entry_data)
        assert response.status_code == 201
        created_entry = response.json()
        entry_id = created_entry["id"]
        assert created_entry["raw_text"] == entry_data["raw_text"]
        print(f"[OK] Entry created with ID: {entry_id}")
        
        # Test entry retrieval
        response = await client.get(f"/api/v1/entries/{entry_id}")
        assert response.status_code == 200
        retrieved_entry = response.json()
        assert retrieved_entry["id"] == entry_id
        print("[OK] Entry retrieval working")
        
        # Test entry listing
        response = await client.get("/api/v1/entries/")
        assert response.status_code == 200
        entries_list = response.json()
        assert "entries" in entries_list
        assert entries_list["total"] >= 1
        print(f"[OK] Entry listing working (found {entries_list['total']} entries)")
        
        # Test entry update
        update_data = {
            "enhanced_text": "This is an enhanced version of the test journal entry.",
            "mode": "enhanced"
        }
        response = await client.put(f"/api/v1/entries/{entry_id}", json=update_data)
        assert response.status_code == 200
        updated_entry = response.json()
        assert updated_entry["enhanced_text"] == update_data["enhanced_text"]
        print("[OK] Entry update working")
        
        # Test entry search
        search_data = {
            "query": "test journal",
            "limit": 10
        }
        response = await client.post("/api/v1/entries/search", json=search_data)
        assert response.status_code == 200
        search_results = response.json()
        assert len(search_results) >= 1
        print(f"[OK] Entry search working (found {len(search_results)} results)")
        
        # Test entry count
        response = await client.get("/api/v1/entries/stats/count")
        assert response.status_code == 200
        count_data = response.json()
        assert count_data["total_entries"] >= 1
        print(f"[OK] Entry count working (total: {count_data['total_entries']})")
        
        print("\n[SUCCESS] All API endpoint tests passed!")


if __name__ == "__main__":
    asyncio.run(test_api_endpoints())
import asyncio
import sys
sys.path.append(".")

from app.db import init_db, EntryRepository, PreferencesRepository
from app.models import Entry


async def test_database():
    """Test database initialization and basic operations"""
    print("Testing database initialization...")
    
    # Initialize database
    await init_db()
    print("[OK] Database initialized successfully")
    
    # Test preferences
    print("\nTesting preferences...")
    hotkey = await PreferencesRepository.get_value("hotkey", "F8")
    print(f"[OK] Default hotkey: {hotkey}")
    
    # Test entry creation
    print("\nTesting entry creation...")
    test_entry = Entry(
        raw_text="This is a test journal entry.",
        mode="raw"
    )
    created_entry = await EntryRepository.create(test_entry)
    print(f"[OK] Created entry with ID: {created_entry.id}")
    
    # Test entry retrieval
    retrieved_entry = await EntryRepository.get_by_id(created_entry.id)
    print(f"[OK] Retrieved entry: {retrieved_entry.raw_text[:30]}...")
    
    # Test entry count
    count = await EntryRepository.count()
    print(f"[OK] Total entries in database: {count}")
    
    print("\n[SUCCESS] All database tests passed!")


if __name__ == "__main__":
    asyncio.run(test_database())
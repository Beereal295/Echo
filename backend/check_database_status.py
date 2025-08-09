#!/usr/bin/env python3
"""
Check current database status and see what entries remain
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from app.db.database import db

async def check_database_status():
    """Check what entries are left in the database"""
    
    # Set database path
    db.db_path = str(Path(__file__).parent / "echo.db")
    await db.connect()
    
    try:
        # Check total entries
        total = await db.fetch_one("SELECT COUNT(*) as count FROM entries")
        print(f"Total entries remaining: {total['count']}")
        
        # Check entries by date
        print("\nEntries by date (last 10 days):")
        for i in range(10):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            count = await db.fetch_one("""
                SELECT COUNT(*) as count FROM entries 
                WHERE DATE(timestamp) = ?
            """, (date_str,))
            if count['count'] > 0:
                print(f"  {date_str}: {count['count']} entries")
        
        # Check ID ranges
        min_max = await db.fetch_one("SELECT MIN(id) as min_id, MAX(id) as max_id FROM entries")
        print(f"\nID range: {min_max['min_id']} - {min_max['max_id']}")
        
        # Check recent entries (by ID)
        recent = await db.fetch_all("""
            SELECT id, timestamp, LEFT(raw_text, 100) as preview 
            FROM entries 
            ORDER BY id DESC 
            LIMIT 20
        """)
        
        print(f"\nMost recent 20 entries:")
        for entry in recent:
            print(f"  ID {entry['id']}: {entry['timestamp']} - {entry['preview']}...")
            
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(check_database_status())
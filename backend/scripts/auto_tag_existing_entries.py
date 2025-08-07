#!/usr/bin/env python3
"""
Auto-Tagging Script for Existing Echo Diary Entries

This script processes all existing entries in the database and adds
smart tags to their processing_metadata without affecting the user experience.
"""

import asyncio
import sqlite3
import json
import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add the parent directory to Python path so we can import our services
sys.path.append(str(Path(__file__).parent.parent))

from app.services.smart_tagging_service import get_smart_tagging_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutoTaggingScript:
    """Script to add smart tags to existing diary entries."""
    
    def __init__(self, db_path: str = "echo.db"):
        """Initialize the auto-tagging script."""
        self.db_path = db_path
        self.smart_tagging_service = get_smart_tagging_service()
        
        # Verify database exists
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        logger.info(f"Initialized auto-tagging script with database: {self.db_path}")
    
    def get_entries_without_smart_tags(self) -> list:
        """Get all entries that don't have smart tags yet."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Get entries that have no smart_tags in the dedicated smart_tags column
            cursor.execute("""
                SELECT id, raw_text, enhanced_text, structured_summary, 
                       processing_metadata, timestamp, mode, word_count, smart_tags
                FROM entries
                WHERE smart_tags IS NULL 
                   OR smart_tags = '[]' 
                   OR smart_tags = ''
                ORDER BY timestamp DESC
            """)
            
            entries = cursor.fetchall()
            logger.info(f"Found {len(entries)} entries without smart tags")
            return [dict(entry) for entry in entries]
            
        finally:
            conn.close()
    
    def update_entry_with_smart_tags(self, entry_id: int, smart_tags: List[str]) -> bool:
        """Update an entry's smart_tags column."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Convert smart tags to JSON
            smart_tags_json = json.dumps(smart_tags)
            
            # Update the entry
            cursor.execute("""
                UPDATE entries 
                SET smart_tags = ?
                WHERE id = ?
            """, (smart_tags_json, entry_id))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.debug(f"Updated entry {entry_id} with smart tags: {smart_tags}")
                return True
            else:
                logger.warning(f"No entry found with id {entry_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update entry {entry_id}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def process_entry(self, entry: Dict[str, Any]) -> bool:
        """Process a single entry and add smart tags."""
        entry_id = entry["id"]
        raw_text = entry["raw_text"]
        
        if not raw_text or not raw_text.strip():
            logger.warning(f"Entry {entry_id} has no raw text, skipping")
            return False
        
        try:
            # Generate smart tags
            smart_tags_result = self.smart_tagging_service.generate_smart_tags(raw_text)
            smart_tags_list = smart_tags_result["tags"]
            
            # Update the entry with just the smart tags list
            success = self.update_entry_with_smart_tags(entry_id, smart_tags_list)
            
            if success:
                tags_str = ", ".join(smart_tags_list) if smart_tags_list else "none"
                logger.info(f"✅ Entry {entry_id}: {tags_str}")
                return True
            else:
                logger.error(f"❌ Failed to update entry {entry_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing entry {entry_id}: {e}")
            return False
    
    def run(self, batch_size: int = 50, max_entries: Optional[int] = None) -> Dict[str, int]:
        """Run the auto-tagging process."""
        logger.info("🚀 Starting auto-tagging process...")
        
        # Get entries to process
        entries = self.get_entries_without_smart_tags()
        
        if not entries:
            logger.info("✅ All entries already have smart tags!")
            return {"processed": 0, "successful": 0, "failed": 0, "skipped": 0}
        
        # Limit entries if specified
        if max_entries and len(entries) > max_entries:
            entries = entries[:max_entries]
            logger.info(f"Limited to processing {max_entries} entries")
        
        # Process entries in batches
        total_entries = len(entries)
        successful = 0
        failed = 0
        skipped = 0
        
        logger.info(f"Processing {total_entries} entries in batches of {batch_size}...")
        
        for i in range(0, total_entries, batch_size):
            batch = entries[i:i + batch_size]
            batch_start = i + 1
            batch_end = min(i + batch_size, total_entries)
            
            logger.info(f"📦 Processing batch {batch_start}-{batch_end} of {total_entries}")
            
            for entry in batch:
                try:
                    result = self.process_entry(entry)
                    if result:
                        successful += 1
                    else:
                        failed += 1
                except Exception as e:
                    logger.error(f"Unexpected error processing entry {entry['id']}: {e}")
                    failed += 1
            
            # Brief pause between batches to avoid overwhelming the system
            if i + batch_size < total_entries:
                logger.info("⏱️  Brief pause between batches...")
                import time
                time.sleep(1)
        
        # Summary
        results = {
            "processed": total_entries,
            "successful": successful,
            "failed": failed,
            "skipped": skipped
        }
        
        logger.info("🎉 Auto-tagging process completed!")
        logger.info(f"📊 Results: {successful} successful, {failed} failed, {skipped} skipped")
        
        return results


def main():
    """Main function to run the auto-tagging script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto-tag existing Echo diary entries")
    parser.add_argument("--db-path", default="echo.db", help="Path to the database file")
    parser.add_argument("--batch-size", type=int, default=50, help="Number of entries to process per batch")
    parser.add_argument("--max-entries", type=int, help="Maximum number of entries to process (for testing)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed without making changes")
    
    args = parser.parse_args()
    
    try:
        # Initialize the script
        script = AutoTaggingScript(db_path=args.db_path)
        
        if args.dry_run:
            logger.info("🔍 DRY RUN MODE - No changes will be made")
            entries = script.get_entries_without_smart_tags()
            
            if not entries:
                logger.info("✅ All entries already have smart tags!")
                return
            
            limit = args.max_entries or len(entries)
            entries_to_show = entries[:limit]
            
            logger.info(f"Would process {len(entries_to_show)} entries:")
            for entry in entries_to_show[:10]:  # Show first 10
                text_preview = (entry["raw_text"] or "")[:50] + "..."
                logger.info(f"  Entry {entry['id']}: {text_preview}")
            
            if len(entries_to_show) > 10:
                logger.info(f"  ... and {len(entries_to_show) - 10} more entries")
                
        else:
            # Run the actual tagging
            results = script.run(
                batch_size=args.batch_size,
                max_entries=args.max_entries
            )
            
            # Show final summary
            if results["successful"] > 0:
                logger.info("✅ Auto-tagging completed successfully!")
                logger.info(f"📈 Tagged {results['successful']} entries with smart tags")
            else:
                logger.warning("⚠️ No entries were successfully tagged")
                
    except FileNotFoundError as e:
        logger.error(f"❌ Database file not found: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("⏹️ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
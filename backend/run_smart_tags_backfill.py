#!/usr/bin/env python3
"""
Simple runner for the smart tags backfill script.
Run this from the backend directory: python run_smart_tags_backfill.py
"""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from auto_tag_existing_entries import AutoTaggingScript

if __name__ == "__main__":
    print("🏷️ Echo Smart Tags - Backward Compatibility Backfill")
    print("This will add smart tags to existing entries without smart_tags.")
    print()
    
    # Confirm before running
    response = input("Continue? (y/N): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        sys.exit(0)
    
    try:
        # Initialize and run the script
        script = AutoTaggingScript()
        results = script.run(batch_size=20)  # Smaller batches for stability
        
        print("\n" + "="*50)
        print("✅ Smart Tags Backfill Complete!")
        print(f"   📝 Processed: {results['processed']} entries")
        print(f"   ✅ Successful: {results['successful']} entries")
        print(f"   ❌ Failed: {results['failed']} entries")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Backfill failed: {e}")
        sys.exit(1)
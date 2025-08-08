#!/usr/bin/env python3
"""
Simple runner for the memory backfill script.
Run this from the backend directory: python run_memory_backfill.py
"""

import asyncio
import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from backfill_memories import main

if __name__ == "__main__":
    print("🧠 Echo Memory System - Backward Compatibility Backfill")
    print("This will process existing entries and conversations to extract memories.")
    print()
    
    # Confirm before running
    response = input("Continue? (y/N): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        sys.exit(0)
    
    # Run the backfill
    asyncio.run(main())
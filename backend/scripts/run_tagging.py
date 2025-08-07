#!/usr/bin/env python3
"""
Simple runner script for auto-tagging existing entries.
Run this from the backend directory.
"""

import os
import sys
from pathlib import Path

def main():
    # Change to backend directory if not already there
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    print("=" * 50)
    print("    Echo Diary - Auto-Tagging Script")
    print("=" * 50)
    print()
    
    # Check if database exists
    if not os.path.exists("echo.db"):
        print("❌ ERROR: echo.db not found in backend directory")
        print("Please make sure you're running this from the correct location")
        return
    
    print("✅ Database found: echo.db")
    print(f"📁 Working directory: {os.getcwd()}")
    print()
    
    # Menu
    print("What would you like to do?")
    print("1. Dry run (see what would be processed)")
    print("2. Process first 10 entries (test)")
    print("3. Process all entries")
    print("4. Exit")
    print()
    
    try:
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == "1":
            print("\n🔍 Running dry run...")
            os.system("python scripts/auto_tag_existing_entries.py --dry-run")
            
        elif choice == "2":
            print("\n🧪 Processing first 10 entries as test...")
            os.system("python scripts/auto_tag_existing_entries.py --max-entries 10")
            
        elif choice == "3":
            print("\n⚠️  This will process ALL entries. Are you sure? (y/N)")
            confirm = input().strip().lower()
            if confirm == 'y':
                print("\n🚀 Processing all entries...")
                os.system("python scripts/auto_tag_existing_entries.py")
            else:
                print("Cancelled.")
                
        elif choice == "4":
            print("Goodbye!")
            return
            
        else:
            print("Invalid choice. Please try again.")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Interrupted by user")
        return
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return
    
    print("\n" + "=" * 50)
    print("Script completed!")
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
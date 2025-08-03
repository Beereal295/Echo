#!/usr/bin/env python3
"""
One-time script to backfill mood tags for existing entries.
This script analyzes all existing entries that don't have mood tags and adds them.

Usage: python backfill_mood_tags.py
"""

import asyncio
import aiosqlite
import json
import requests
import sys
from datetime import datetime
from typing import List, Optional


# Configuration - adjust these if needed
DB_PATH = "./echo.db"  # Path to your database file
OLLAMA_BASE_URL = "http://localhost:11434"  # Your Ollama server URL
OLLAMA_MODEL = "mistral:latest"  # Your preferred model
OLLAMA_TEMPERATURE = 0.2
OLLAMA_CONTEXT_WINDOW = 4096

# The same mood analysis prompt used in the application
MOOD_SYSTEM_PROMPT = """You are a mood and emotion analyzer for personal journal entries. Your task is to identify the emotional states and moods expressed in the text.

INSTRUCTIONS:
1. Analyze the emotional content of the journal entry
2. Identify specific moods and emotional states
3. Return ONLY a JSON array of mood tags
4. Use simple, clear mood words (e.g., "happy", "stressed", "excited", "anxious", "grateful", "tired", "frustrated", "content", "overwhelmed", "peaceful")
5. Include 1-5 mood tags maximum
6. Focus on the dominant emotions expressed
7. Use consistent mood vocabulary

FORBIDDEN:
- Do not add explanations or commentary
- Do not include non-emotional descriptors
- Do not repeat similar moods
- Do not include activities or events, only emotions

EXAMPLE OUTPUT:
["happy", "excited", "grateful"]

Return only the JSON array, nothing else."""


class MoodBackfillService:
    def __init__(self):
        self.db_path = DB_PATH
        self.ollama_url = f"{OLLAMA_BASE_URL}/api/generate"
        self.processed_count = 0
        self.failed_count = 0
        self.skipped_count = 0

    async def analyze_mood_with_ollama(self, text: str) -> List[str]:
        """
        Call Ollama API directly to analyze mood from text.
        Returns list of mood tags.
        """
        if not text or not text.strip():
            return []

        try:
            # Prepare request payload
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": text,
                "system": MOOD_SYSTEM_PROMPT,
                "stream": False,
                "options": {
                    "temperature": OLLAMA_TEMPERATURE,
                    "num_ctx": OLLAMA_CONTEXT_WINDOW
                }
            }

            # Make request to Ollama
            print(f"  📝 Analyzing mood with Ollama...")
            response = requests.post(
                self.ollama_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"  ❌ Ollama API error: {response.status_code} - {response.text}")
                return []

            result = response.json()
            mood_response = result.get("response", "").strip()
            
            # Parse the mood response
            mood_tags = self._parse_mood_response(mood_response)
            print(f"  🏷️ Extracted moods: {mood_tags}")
            return mood_tags

        except requests.exceptions.RequestException as e:
            print(f"  ❌ Network error calling Ollama: {e}")
            return []
        except Exception as e:
            print(f"  ❌ Error analyzing mood: {e}")
            return []

    def _parse_mood_response(self, response: str) -> List[str]:
        """Parse the LLM response to extract mood tags."""
        try:
            # Try to parse as JSON first
            if response.startswith('[') and response.endswith(']'):
                mood_tags = json.loads(response)
                if isinstance(mood_tags, list):
                    # Clean and validate mood tags
                    cleaned_moods = []
                    for mood in mood_tags:
                        if isinstance(mood, str) and mood.strip():
                            cleaned_mood = mood.strip().lower()
                            # Basic validation - single word moods only
                            if len(cleaned_mood.split()) == 1 and len(cleaned_mood) <= 20:
                                cleaned_moods.append(cleaned_mood)
                    
                    return cleaned_moods[:5]  # Maximum 5 moods
            
            # Fallback: try to extract words from response
            words = response.lower().replace('[', '').replace(']', '').replace('"', '').replace("'", '')
            mood_candidates = [word.strip() for word in words.split(',')]
            
            # Filter valid mood words
            moods = []
            common_moods = {
                'happy', 'sad', 'excited', 'anxious', 'stressed', 'calm', 'angry', 'frustrated',
                'grateful', 'tired', 'energetic', 'peaceful', 'overwhelmed', 'content', 'worried',
                'hopeful', 'disappointed', 'proud', 'confused', 'relieved', 'nervous', 'confident',
                'lonely', 'loved', 'inspired', 'bored', 'surprised', 'scared', 'optimistic'
            }
            
            for mood in mood_candidates:
                clean_mood = mood.strip().lower()
                if clean_mood in common_moods and clean_mood not in moods:
                    moods.append(clean_mood)
                    if len(moods) >= 5:
                        break
            
            return moods
        
        except Exception as e:
            print(f"  ⚠️ Failed to parse mood response '{response}': {e}")
            return []

    async def get_entries_without_moods(self, db: aiosqlite.Connection) -> List[dict]:
        """Get all entries that don't have mood tags."""
        cursor = await db.execute("""
            SELECT id, raw_text, enhanced_text, structured_summary, timestamp 
            FROM entries 
            WHERE mood_tags IS NULL OR mood_tags = '' OR mood_tags = '[]'
            ORDER BY timestamp ASC
        """)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def update_entry_moods(self, db: aiosqlite.Connection, entry_id: int, mood_tags: List[str]):
        """Update an entry with mood tags."""
        mood_json = json.dumps(mood_tags) if mood_tags else None
        await db.execute(
            "UPDATE entries SET mood_tags = ? WHERE id = ?",
            (mood_json, entry_id)
        )
        await db.commit()

    async def test_ollama_connection(self):
        """Test if Ollama is available."""
        try:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            if response.status_code == 200:
                print(f"✅ Ollama connection successful at {OLLAMA_BASE_URL}")
                
                # Check if the model is available
                models = response.json().get("models", [])
                model_names = [model.get("name", "") for model in models]
                if OLLAMA_MODEL in model_names:
                    print(f"✅ Model '{OLLAMA_MODEL}' is available")
                    return True
                else:
                    print(f"❌ Model '{OLLAMA_MODEL}' not found. Available models: {model_names}")
                    return False
            else:
                print(f"❌ Ollama connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to Ollama at {OLLAMA_BASE_URL}: {e}")
            return False

    async def run_backfill(self):
        """Run the mood tag backfill process."""
        print("🔥 Starting mood tag backfill process...")
        print(f"📂 Database: {self.db_path}")
        print(f"🤖 Ollama: {OLLAMA_BASE_URL}")
        print(f"🧠 Model: {OLLAMA_MODEL}")
        print("-" * 50)

        # Test Ollama connection first
        if not await self.test_ollama_connection():
            print("\n❌ Cannot proceed without Ollama connection. Please check your setup.")
            return False

        # Connect to database
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                # Get entries without mood tags
                print("\n📊 Finding entries without mood tags...")
                entries = await self.get_entries_without_moods(db)
                
                if not entries:
                    print("✅ All entries already have mood tags! Nothing to backfill.")
                    return True

                print(f"📝 Found {len(entries)} entries to process")
                
                # Confirm before proceeding
                print(f"\n⚠️  This will make {len(entries)} individual API calls to Ollama.")
                print("   Each call may take a few seconds.")
                confirm = input("   Continue? (y/N): ").strip().lower()
                
                if confirm != 'y':
                    print("🚫 Backfill cancelled by user")
                    return False

                print("\n🚀 Starting backfill process...\n")

                # Process each entry
                for i, entry in enumerate(entries, 1):
                    entry_id = entry['id']
                    timestamp = entry['timestamp']
                    
                    print(f"[{i}/{len(entries)}] Processing entry {entry_id} ({timestamp})...")
                    
                    # Get text to analyze (prefer enhanced, fall back to raw)
                    text_to_analyze = entry.get('enhanced_text') or entry.get('raw_text')
                    
                    if not text_to_analyze or not text_to_analyze.strip():
                        print(f"  ⚠️ Skipping entry {entry_id} - no text content")
                        self.skipped_count += 1
                        continue
                    
                    # Show preview of text
                    preview = text_to_analyze[:100] + "..." if len(text_to_analyze) > 100 else text_to_analyze
                    print(f"  📄 Text preview: {preview}")
                    
                    # Analyze mood
                    mood_tags = await self.analyze_mood_with_ollama(text_to_analyze)
                    
                    if mood_tags:
                        # Update database
                        await self.update_entry_moods(db, entry_id, mood_tags)
                        print(f"  ✅ Updated entry {entry_id} with moods: {mood_tags}")
                        self.processed_count += 1
                    else:
                        print(f"  ⚠️ No moods extracted for entry {entry_id}")
                        self.failed_count += 1
                    
                    print()  # Add spacing between entries
                
                # Print summary
                print("=" * 50)
                print("📊 BACKFILL SUMMARY")
                print("=" * 50)
                print(f"✅ Successfully processed: {self.processed_count}")
                print(f"⚠️ Failed to extract moods: {self.failed_count}")
                print(f"⏭️ Skipped (no content): {self.skipped_count}")
                print(f"📝 Total entries processed: {len(entries)}")
                print("=" * 50)
                
                if self.processed_count > 0:
                    print("🎉 Mood tag backfill completed successfully!")
                else:
                    print("⚠️ No entries were updated with mood tags.")
                
                return True

        except Exception as e:
            print(f"\n❌ Database error: {e}")
            return False


async def main():
    """Main function."""
    print("🔥 Echo Journal - Mood Tag Backfill Script")
    print("=" * 50)
    
    service = MoodBackfillService()
    success = await service.run_backfill()
    
    if not success:
        sys.exit(1)
    
    print("\n✅ Script completed successfully!")


if __name__ == "__main__":
    # Run the backfill process
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🚫 Script cancelled by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
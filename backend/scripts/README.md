# Echo Diary Auto-Tagging Scripts

This directory contains scripts to automatically add smart tags to existing diary entries.

## Files

- **`auto_tag_existing_entries.py`** - Main auto-tagging script
- **`run_tagging.py`** - Simple Python runner with menu
- **`run_auto_tagging.bat`** - Windows batch file runner
- **`README.md`** - This file

## What does Auto-Tagging do?

The auto-tagging system analyzes existing diary entries and automatically adds semantic tags like:

- `idea` - Ideas, concepts, innovations
- `todo` - Action items, tasks, TODOs
- `question` - Questions and inquiries
- `decision` - Decisions made
- `learning` - Things learned, insights
- `reference` - Links, resources, books
- `meeting` - Meeting notes
- `project:*` - Project-specific mentions

These tags are stored in the `processing_metadata` field and are **not visible to users** in the frontend. They enable powerful search and analysis tools in the "Talk to Your Diary" feature.

## How to Run

### Option 1: Simple Python Runner (Recommended)
```bash
cd backend
python scripts/run_tagging.py
```

### Option 2: Windows Batch File
```bash
cd backend
scripts/run_auto_tagging.bat
```

### Option 3: Direct Script Execution
```bash
cd backend

# Dry run (see what would be processed)
python scripts/auto_tag_existing_entries.py --dry-run

# Process first 10 entries (test)
python scripts/auto_tag_existing_entries.py --max-entries 10

# Process all entries
python scripts/auto_tag_existing_entries.py

# Custom batch size
python scripts/auto_tag_existing_entries.py --batch-size 25
```

## Command Line Options

- `--db-path PATH` - Path to database file (default: echo.db)
- `--batch-size N` - Process N entries per batch (default: 50)
- `--max-entries N` - Limit processing to N entries (for testing)
- `--dry-run` - Show what would be processed without making changes

## Safety Features

- **Dry run mode** - Test without making changes
- **Batch processing** - Processes entries in small batches
- **Existing data preservation** - Won't overwrite existing metadata
- **Error handling** - Continues processing if individual entries fail
- **Logging** - Detailed progress and error logs

## Example Output

```
🚀 Starting auto-tagging process...
📦 Processing batch 1-50 of 234
✅ Entry 123: idea, project:startup, todo
✅ Entry 124: question, learning
✅ Entry 125: meeting, decision
...
🎉 Auto-tagging process completed!
📊 Results: 234 successful, 0 failed, 0 skipped
```

## What Gets Tagged

The smart tagging system looks for patterns like:

- **Ideas**: "idea", "concept", "what if", "innovation"
- **TODOs**: "todo", "need to", "should", "must", "task"
- **Questions**: Text containing "?"
- **Decisions**: "decided", "going with", "will do"
- **Learning**: "learned", "TIL", "discovered", "insight"
- **References**: URLs, "book", "article", "resource"
- **Meetings**: "meeting", "call", "agenda", "attendees"

## After Running

Once auto-tagging is complete, users can use powerful new chat commands:

- "What ideas have I had about machine learning?"
- "Show me my action items from last week"
- "Extract my thoughts on the startup"
- "What decisions have I made recently?"

The smart tags enable these AI-powered analysis tools to work much more effectively!

## Troubleshooting

- **Database not found**: Make sure you're in the `backend` directory
- **Import errors**: Ensure you have all dependencies installed
- **Permission errors**: Run as administrator if needed on Windows
- **Memory issues**: Use smaller `--batch-size` for large datasets
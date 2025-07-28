from .entry_repository import EntryRepository
from .pattern_repository import PatternRepository
from .preferences_repository import PreferencesRepository
from .draft_repository import DraftRepository
from app.db.database import db

# Repository instances
_preferences_repo = None

async def get_preferences_repository() -> PreferencesRepository:
    """Get global preferences repository instance"""
    global _preferences_repo
    if _preferences_repo is None:
        _preferences_repo = PreferencesRepository(db)
    return _preferences_repo

__all__ = [
    "EntryRepository",
    "PatternRepository", 
    "PreferencesRepository",
    "DraftRepository",
    "get_preferences_repository"
]
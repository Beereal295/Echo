from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import json


@dataclass
class Entry:
    """Journal entry model"""
    id: Optional[int] = None
    raw_text: str = ""
    enhanced_text: Optional[str] = None
    structured_summary: Optional[str] = None
    mode: str = "raw"  # raw, enhanced, structured
    embeddings: Optional[List[float]] = None
    timestamp: datetime = None
    mood_tags: Optional[List[str]] = None
    word_count: int = 0
    processing_metadata: Optional[dict] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.mood_tags is None:
            self.mood_tags = []
        if self.processing_metadata is None:
            self.processing_metadata = {}
        if self.word_count == 0 and self.raw_text:
            self.word_count = len(self.raw_text.split())
    
    def to_dict(self):
        """Convert to dictionary for database storage"""
        return {
            "id": self.id,
            "raw_text": self.raw_text,
            "enhanced_text": self.enhanced_text,
            "structured_summary": self.structured_summary,
            "mode": self.mode,
            "embeddings": json.dumps(self.embeddings) if self.embeddings else None,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "mood_tags": json.dumps(self.mood_tags) if self.mood_tags else None,
            "word_count": self.word_count,
            "processing_metadata": json.dumps(self.processing_metadata) if self.processing_metadata else None
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create Entry from database row"""
        # Parse JSON fields
        if data.get("embeddings"):
            data["embeddings"] = json.loads(data["embeddings"])
        if data.get("mood_tags"):
            data["mood_tags"] = json.loads(data["mood_tags"])
        if data.get("processing_metadata"):
            data["processing_metadata"] = json.loads(data["processing_metadata"])
        if data.get("timestamp"):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        
        return cls(**data)
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import json


@dataclass
class Conversation:
    """Conversation model for Talk to Your Diary feature"""
    id: Optional[int] = None
    timestamp: datetime = None
    duration: int = 0  # in seconds
    transcription: str = ""
    conversation_type: str = "chat"  # 'call' or 'chat'
    message_count: int = 0
    search_queries_used: Optional[List[str]] = None
    created_at: datetime = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.search_queries_used is None:
            self.search_queries_used = []
    
    def to_dict(self):
        """Convert to dictionary for database storage"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "duration": self.duration,
            "transcription": self.transcription,
            "conversation_type": self.conversation_type,
            "message_count": self.message_count,
            "search_queries_used": json.dumps(self.search_queries_used) if self.search_queries_used else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def add_search_query(self, query: str):
        """Add a search query to the list"""
        if self.search_queries_used is None:
            self.search_queries_used = []
        if query not in self.search_queries_used:
            self.search_queries_used.append(query)
    
    def update_duration(self, duration_seconds: int):
        """Update conversation duration"""
        self.duration = duration_seconds
        self.updated_at = datetime.now()
    
    def increment_message_count(self):
        """Increment message count and update timestamp"""
        self.message_count += 1
        self.updated_at = datetime.now()
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create Conversation from database row"""
        # Parse JSON fields
        if data.get("search_queries_used"):
            data["search_queries_used"] = json.loads(data["search_queries_used"])
        
        # Parse datetime fields
        if data.get("timestamp"):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        
        return cls(**data)
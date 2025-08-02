import aiosqlite
from typing import Optional
from datetime import datetime

from app.core.config import settings
from app.db.schema import ALL_TABLES, INDEXES
from app.db.migrations import run_migrations as run_db_migrations


class Database:
    def __init__(self):
        self.db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self):
        """Create database connection"""
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        await self._connection.execute("PRAGMA foreign_keys = ON")
    
    async def disconnect(self):
        """Close database connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def execute(self, query: str, params: tuple = ()):
        """Execute a query"""
        if not self._connection:
            await self.connect()
        return await self._connection.execute(query, params)
    
    async def execute_many(self, query: str, params: list[tuple]):
        """Execute many queries"""
        if not self._connection:
            await self.connect()
        return await self._connection.executemany(query, params)
    
    async def fetch_one(self, query: str, params: tuple = ()):
        """Fetch one row"""
        cursor = await self.execute(query, params)
        row = await cursor.fetchone()
        return dict(row) if row else None
    
    async def fetch_all(self, query: str, params: tuple = ()):
        """Fetch all rows"""
        cursor = await self.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def commit(self):
        """Commit transaction"""
        if self._connection:
            await self._connection.commit()
    
    async def rollback(self):
        """Rollback transaction"""
        if self._connection:
            await self._connection.rollback()


# Global database instance
db = Database()


async def create_tables():
    """Create all database tables"""
    # Create tables
    for table_sql in ALL_TABLES:
        await db.execute(table_sql)
    
    # Create indexes
    for index_sql in INDEXES:
        await db.execute(index_sql)
    
    await db.commit()


async def run_migrations():
    """Run database migrations"""
    await run_db_migrations(db)


async def init_db():
    """Initialize database with schema"""
    await db.connect()
    
    # Create tables
    await create_tables()
    
    # Run migrations
    await run_migrations()
    
    # Insert default preferences
    await initialize_default_preferences()
    
    print("Database initialized successfully")


async def initialize_default_preferences():
    """Insert default preference values"""
    default_prefs = [
        ("hotkey", "F8", "string", "Global hotkey for voice recording"),
        ("ollama_port", "11434", "int", "Ollama server port"),
        ("ollama_model", "llama2", "string", "Default Ollama model"),
        ("whisper_model", "base", "string", "Whisper model size"),
        ("pattern_unlock_shown", "false", "bool", "Whether pattern unlock celebration was shown"),
        ("coffee_popup_shown", "false", "bool", "Whether coffee popup was shown"),
        ("coffee_popup_dismissed_date", "", "string", "Last date coffee popup was dismissed"),
        ("first_use_date", datetime.now().isoformat(), "string", "First use date of the application"),
        ("pattern_detection_threshold", "30", "int", "Number of entries required for pattern detection"),
    ]
    
    for key, value, value_type, description in default_prefs:
        # Check if preference already exists
        existing = await db.fetch_one(
            "SELECT id FROM preferences WHERE key = ?", (key,)
        )
        if not existing:
            await db.execute(
                """INSERT INTO preferences (key, value, value_type, description) 
                   VALUES (?, ?, ?, ?)""",
                (key, value, value_type, description)
            )
    
    await db.commit()
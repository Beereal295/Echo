import aiosqlite
from typing import Optional

from app.core.config import settings


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


# Global database instance
db = Database()


async def init_db():
    """Initialize database with schema"""
    await db.connect()
    
    # Will be implemented in Task 1.2
    # For now, just ensure connection works
    
    print("Database initialized successfully")
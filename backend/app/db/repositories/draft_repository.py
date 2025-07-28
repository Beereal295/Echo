from typing import Optional
from datetime import datetime

from app.db.database import db
from app.models.draft import Draft


class DraftRepository:
    """Repository for draft database operations"""
    
    @staticmethod
    async def create(draft: Draft) -> Draft:
        """Create a new draft"""
        data = draft.to_dict()
        del data["id"]
        
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        values = list(data.values())
        
        cursor = await db.execute(
            f"INSERT INTO drafts ({columns}) VALUES ({placeholders})",
            tuple(values)
        )
        await db.commit()
        
        draft.id = cursor.lastrowid
        return draft
    
    @staticmethod
    async def get_latest() -> Optional[Draft]:
        """Get the most recent draft"""
        row = await db.fetch_one(
            """SELECT * FROM drafts 
               ORDER BY updated_at DESC, created_at DESC 
               LIMIT 1"""
        )
        return Draft.from_dict(row) if row else None
    
    @staticmethod
    async def get_by_id(draft_id: int) -> Optional[Draft]:
        """Get draft by ID"""
        row = await db.fetch_one(
            "SELECT * FROM drafts WHERE id = ?", (draft_id,)
        )
        return Draft.from_dict(row) if row else None
    
    @staticmethod
    async def update(draft: Draft) -> Draft:
        """Update an existing draft"""
        draft.updated_at = datetime.now()
        data = draft.to_dict()
        draft_id = data.pop("id")
        
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        values = list(data.values())
        values.append(draft_id)
        
        await db.execute(
            f"UPDATE drafts SET {set_clause} WHERE id = ?",
            tuple(values)
        )
        await db.commit()
        
        return draft
    
    @staticmethod
    async def save_or_update(content: str, metadata: Optional[dict] = None) -> Draft:
        """Save draft content, updating existing draft if recent enough"""
        latest = await DraftRepository.get_latest()
        
        # If there's a recent draft (within last 5 minutes), update it
        if latest and latest.created_at:
            time_diff = datetime.now() - latest.created_at
            if time_diff.total_seconds() < 300:  # 5 minutes
                latest.content = content
                latest.metadata = metadata or latest.metadata
                return await DraftRepository.update(latest)
        
        # Otherwise create a new draft
        draft = Draft(content=content, metadata=metadata)
        return await DraftRepository.create(draft)
    
    @staticmethod
    async def delete(draft_id: int) -> bool:
        """Delete a draft"""
        await db.execute("DELETE FROM drafts WHERE id = ?", (draft_id,))
        await db.commit()
        return True
    
    @staticmethod
    async def delete_old_drafts(days: int = 7) -> int:
        """Delete drafts older than specified days"""
        cutoff_date = datetime.now()
        cutoff_date = cutoff_date.replace(
            day=cutoff_date.day - days if cutoff_date.day > days else 1
        )
        
        cursor = await db.execute(
            "DELETE FROM drafts WHERE created_at < ?",
            (cutoff_date.isoformat(),)
        )
        await db.commit()
        
        return cursor.rowcount
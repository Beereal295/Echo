from fastapi import APIRouter, HTTPException
from typing import List, Optional

from app.api.schemas import SuccessResponse
from app.services.patterns import PatternDetector, PatternType
from app.db.repositories import get_preferences_repository

router = APIRouter(prefix="/patterns", tags=["patterns"])


@router.get("/check", response_model=SuccessResponse)
async def check_pattern_threshold():
    """Check if pattern detection threshold is met"""
    try:
        pattern_detector = PatternDetector()
        preferences_repo = await get_preferences_repository()
        
        # Get threshold from preferences
        threshold = await preferences_repo.get_value(
            "pattern_detection_threshold", default=30
        )
        
        # Check if threshold is met
        is_met = await pattern_detector.check_threshold_met(threshold)
        
        # Get current entry count
        from app.db.database import db
        result = await db.fetch_one("SELECT COUNT(*) as count FROM entries")
        entry_count = result["count"] if result else 0
        
        return SuccessResponse(
            message=f"Pattern detection {'enabled' if is_met else 'disabled'}",
            data={
                "threshold_met": is_met,
                "threshold": threshold,
                "entry_count": entry_count,
                "remaining": max(0, threshold - entry_count) if not is_met else 0
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check pattern threshold: {str(e)}")


@router.post("/analyze", response_model=SuccessResponse)
async def analyze_patterns():
    """Manually trigger pattern analysis"""
    try:
        pattern_detector = PatternDetector()
        preferences_repo = await get_preferences_repository()
        
        # Get threshold from preferences
        threshold = await preferences_repo.get_value(
            "pattern_detection_threshold", default=30
        )
        
        # Check if threshold is met
        if not await pattern_detector.check_threshold_met(threshold):
            raise HTTPException(
                status_code=400, 
                detail=f"Pattern detection requires at least {threshold} entries"
            )
        
        # Run pattern analysis
        try:
            patterns = await pattern_detector.analyze_entries(min_entries=threshold)
            
            return SuccessResponse(
                message=f"Pattern analysis complete",
                data={
                    "patterns_found": len(patterns),
                    "pattern_types": {
                        pattern_type.value: sum(1 for p in patterns if p.pattern_type == pattern_type)
                        for pattern_type in PatternType
                    }
                }
            )
        except Exception as analysis_error:
            print(f"Pattern analysis error: {analysis_error}")
            raise HTTPException(status_code=500, detail=f"Pattern analysis failed: {str(analysis_error)}")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze patterns: {str(e)}")


@router.get("/", response_model=SuccessResponse)
async def get_patterns():
    """Get all detected patterns"""
    try:
        pattern_detector = PatternDetector()
        patterns = await pattern_detector.get_patterns()
        
        # Convert patterns to response format
        pattern_data = []
        for pattern in patterns:
            data = pattern.to_dict()
            # Ensure JSON fields are parsed
            import json
            if isinstance(data.get("related_entries"), str):
                data["related_entries"] = json.loads(data["related_entries"])
            if isinstance(data.get("keywords"), str):
                data["keywords"] = json.loads(data["keywords"])
            pattern_data.append(data)
        
        return SuccessResponse(
            message=f"Retrieved {len(pattern_data)} patterns",
            data={
                "patterns": pattern_data,
                "total": len(pattern_data)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patterns: {str(e)}")


@router.get("/entries/{pattern_id}", response_model=SuccessResponse)
async def get_pattern_entries(pattern_id: int):
    """Get entries related to a specific pattern"""
    try:
        from app.db.database import db
        import json
        
        # Get pattern
        pattern_row = await db.fetch_one(
            "SELECT * FROM patterns WHERE id = ?", (pattern_id,)
        )
        
        if not pattern_row:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        # Parse related entries
        related_entries = json.loads(pattern_row["related_entries"])
        
        if not related_entries:
            return SuccessResponse(
                message=f"No entries found for pattern {pattern_id}",
                data={
                    "entries": [],
                    "pattern_id": pattern_id,
                    "total": 0
                }
            )
        
        # Fetch entries
        placeholders = ", ".join(["?" for _ in related_entries])
        entries = await db.fetch_all(
            f"""SELECT id, raw_text, enhanced_text, structured_summary, 
                       timestamp, mood_tags, word_count
                FROM entries 
                WHERE id IN ({placeholders})
                ORDER BY timestamp DESC""",
            tuple(related_entries)
        )
        
        # Convert to response format
        entry_data = []
        for entry in entries:
            data = dict(entry)
            if data.get("mood_tags"):
                data["mood_tags"] = json.loads(data["mood_tags"])
            entry_data.append(data)
        
        return SuccessResponse(
            message=f"Retrieved {len(entry_data)} entries for pattern {pattern_id}",
            data={
                "entries": entry_data,
                "pattern_id": pattern_id,
                "total": len(entry_data)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pattern entries: {str(e)}")
from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, List
from datetime import datetime

from app.api.schemas import (
    EntryCreate,
    EntryUpdate,
    EntryResponse,
    EntryListResponse,
    EntrySearchRequest,
    SuccessResponse,
    ErrorResponse
)
from app.db import EntryRepository
from app.models.entry import Entry
from app.schemas.entry import ProcessingMode, EntryProcessRequest, EntryCreateAndProcessRequest
# Note: Using our newer schema definitions that include ProcessingMode enum
from app.services.entry_processing import get_entry_processing_service
from app.services.processing_queue import get_processing_queue

router = APIRouter(prefix="/entries", tags=["entries"])


@router.post("/", response_model=EntryResponse, status_code=201)
async def create_entry(entry_data: EntryCreate):
    """Create a new journal entry"""
    try:
        # Create entry model with basic data
        # Handle mode as string (from API schema) 
        mode_str = entry_data.mode if isinstance(entry_data.mode, str) else entry_data.mode.value
        entry = Entry(
            raw_text=entry_data.raw_text,
            mode=mode_str,
            timestamp=datetime.now(),
            word_count=len(entry_data.raw_text.split())
        )
        
        # Save to database first
        created_entry = await EntryRepository.create(entry)
        
        # Convert to response format
        return EntryResponse(
            id=created_entry.id,
            raw_text=created_entry.raw_text,
            enhanced_text=created_entry.enhanced_text,
            structured_summary=created_entry.structured_summary,
            mode=created_entry.mode,
            embeddings=created_entry.embeddings,
            timestamp=created_entry.timestamp,
            mood_tags=created_entry.mood_tags,
            word_count=created_entry.word_count,
            processing_metadata=created_entry.processing_metadata
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create entry: {str(e)}")


@router.get("/", response_model=EntryListResponse)
async def list_entries(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    mode: Optional[str] = Query(None, description="Filter by processing mode")
):
    """List journal entries with pagination"""
    try:
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get entries
        entries = await EntryRepository.get_all(
            limit=page_size,
            offset=offset,
            mode=mode
        )
        
        # Get total count for pagination
        total = await EntryRepository.count()
        
        # Convert to response format
        entry_responses = [
            EntryResponse(
                id=entry.id,
                raw_text=entry.raw_text,
                enhanced_text=entry.enhanced_text,
                structured_summary=entry.structured_summary,
                mode=entry.mode,
                embeddings=entry.embeddings,
                timestamp=entry.timestamp,
                mood_tags=entry.mood_tags,
                word_count=entry.word_count,
                processing_metadata=entry.processing_metadata
            )
            for entry in entries
        ]
        
        return EntryListResponse(
            entries=entry_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_next=offset + page_size < total,
            has_prev=page > 1
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list entries: {str(e)}")


@router.get("/{entry_id}", response_model=EntryResponse)
async def get_entry(entry_id: int = Path(..., description="Entry ID")):
    """Get a specific journal entry by ID"""
    try:
        entry = await EntryRepository.get_by_id(entry_id)
        
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        return EntryResponse(
            id=entry.id,
            raw_text=entry.raw_text,
            enhanced_text=entry.enhanced_text,
            structured_summary=entry.structured_summary,
            mode=entry.mode,
            embeddings=entry.embeddings,
            timestamp=entry.timestamp,
            mood_tags=entry.mood_tags,
            word_count=entry.word_count,
            processing_metadata=entry.processing_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entry: {str(e)}")


@router.put("/{entry_id}", response_model=EntryResponse)
async def update_entry(
    entry_id: int = Path(..., description="Entry ID"),
    entry_data: EntryUpdate = ...
):
    """Update a journal entry"""
    try:
        # Get existing entry
        entry = await EntryRepository.get_by_id(entry_id)
        
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        # Update fields that were provided
        if entry_data.raw_text is not None:
            entry.raw_text = entry_data.raw_text
            entry.word_count = len(entry_data.raw_text.split())
        
        if entry_data.enhanced_text is not None:
            entry.enhanced_text = entry_data.enhanced_text
            
        if entry_data.structured_summary is not None:
            entry.structured_summary = entry_data.structured_summary
            
        if entry_data.mode is not None:
            entry.mode = entry_data.mode if isinstance(entry_data.mode, str) else entry_data.mode.value
            
        if entry_data.mood_tags is not None:
            entry.mood_tags = entry_data.mood_tags
        
        # Save updates
        updated_entry = await EntryRepository.update(entry)
        
        return EntryResponse(
            id=updated_entry.id,
            raw_text=updated_entry.raw_text,
            enhanced_text=updated_entry.enhanced_text,
            structured_summary=updated_entry.structured_summary,
            mode=updated_entry.mode,
            embeddings=updated_entry.embeddings,
            timestamp=updated_entry.timestamp,
            mood_tags=updated_entry.mood_tags,
            word_count=updated_entry.word_count,
            processing_metadata=updated_entry.processing_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update entry: {str(e)}")


@router.delete("/{entry_id}", response_model=SuccessResponse)
async def delete_entry(entry_id: int = Path(..., description="Entry ID")):
    """Delete a journal entry"""
    try:
        # Check if entry exists
        entry = await EntryRepository.get_by_id(entry_id)
        
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        # Delete entry
        await EntryRepository.delete(entry_id)
        
        return SuccessResponse(
            message="Entry deleted successfully",
            data={"id": entry_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete entry: {str(e)}")


@router.post("/search", response_model=List[EntryResponse])
async def search_entries(search_request: EntrySearchRequest):
    """Search journal entries by text content"""
    try:
        entries = await EntryRepository.search(
            query=search_request.query,
            limit=search_request.limit
        )
        
        return [
            EntryResponse(
                id=entry.id,
                raw_text=entry.raw_text,
                enhanced_text=entry.enhanced_text,
                structured_summary=entry.structured_summary,
                mode=entry.mode,
                embeddings=entry.embeddings,
                timestamp=entry.timestamp,
                mood_tags=entry.mood_tags,
                word_count=entry.word_count,
                processing_metadata=entry.processing_metadata
            )
            for entry in entries
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search entries: {str(e)}")


@router.post("/process/{entry_id}", response_model=dict)
async def process_entry(
    entry_id: int = Path(..., description="Entry ID"),
    process_request: EntryProcessRequest = ...
):
    """Queue an entry for processing with specified mode (enhanced or structured)"""
    try:
        # Get existing entry
        entry = await EntryRepository.get_by_id(entry_id)
        
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        # Add to processing queue
        processing_queue = await get_processing_queue()
        job_id = await processing_queue.add_job(
            entry_id=entry_id,
            mode=process_request.mode,
            raw_text=entry.raw_text
        )
        
        return {
            "message": "Entry queued for processing",
            "job_id": job_id,
            "entry_id": entry_id,
            "mode": process_request.mode.value,
            "status": "pending"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue entry for processing: {str(e)}")


@router.post("/create-and-process", response_model=dict)
async def create_and_process_entry(
    request: EntryCreateAndProcessRequest
):
    """Create a new entry and queue it for processing in specified modes"""
    try:
        # Create raw entry first
        entry = Entry(
            raw_text=request.raw_text,
            mode="raw",
            timestamp=datetime.now(),
            word_count=len(request.raw_text.split())
        )
        
        created_entry = await EntryRepository.create(entry)
        
        # Queue for processing in each requested mode
        processing_queue = await get_processing_queue()
        job_ids = []
        
        for mode in request.modes:
            if mode != ProcessingMode.RAW:  # Skip raw mode
                job_id = await processing_queue.add_job(
                    entry_id=created_entry.id,
                    mode=mode,
                    raw_text=request.raw_text
                )
                job_ids.append({"mode": mode.value, "job_id": job_id})
        
        # Create a master job ID that combines all jobs for easier tracking
        master_job_id = f"master_{created_entry.id}_{datetime.now().timestamp()}"
        
        return {
            "message": "Entry created and queued for processing",
            "entry_id": created_entry.id,
            "job_id": master_job_id,  # Add this for frontend compatibility
            "jobs": job_ids,
            "raw_entry": {
                "id": created_entry.id,
                "raw_text": created_entry.raw_text,
                "timestamp": created_entry.timestamp,
                "word_count": created_entry.word_count
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create and process entry: {str(e)}")


@router.get("/processing/job/{job_id}", response_model=dict)
async def get_processing_job_status(job_id: str = Path(..., description="Job ID")):
    """Get the status of a processing job"""
    try:
        processing_queue = await get_processing_queue()
        
        # Handle master job IDs (format: master_{entry_id}_{timestamp})
        if job_id.startswith("master_"):
            parts = job_id.split("_")
            if len(parts) >= 3:
                entry_id = int(parts[1])
                
                # Get the entry to check current state
                entry = await EntryRepository.get_by_id(entry_id)
                if not entry:
                    raise HTTPException(status_code=404, detail="Entry not found")
                
                # Check if both enhanced and structured are complete
                has_enhanced = entry.enhanced_text is not None
                has_structured = entry.structured_summary is not None
                
                if has_enhanced and has_structured:
                    # Both processing modes complete
                    return {
                        "id": job_id,
                        "entry_id": entry_id,
                        "status": "completed",
                        "result": {
                            "entry_id": entry_id,
                            "enhanced": entry.enhanced_text,
                            "structured": entry.structured_summary
                        }
                    }
                else:
                    # Still processing
                    return {
                        "id": job_id,
                        "entry_id": entry_id,
                        "status": "processing",
                        "result": None
                    }
        
        # Handle regular job IDs
        job = processing_queue.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.get("/processing/queue/status", response_model=dict)
async def get_queue_status():
    """Get the status of the processing queue"""
    try:
        processing_queue = await get_processing_queue()
        return processing_queue.get_queue_status()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue status: {str(e)}")


@router.get("/stats/count", response_model=dict)
async def get_entry_count():
    """Get total count of entries"""
    try:
        count = await EntryRepository.count()
        return {"total_entries": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entry count: {str(e)}")
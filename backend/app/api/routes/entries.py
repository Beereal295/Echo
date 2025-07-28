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
from app.schemas.entry import ProcessingMode, EntryProcessRequest
# Note: Using our newer schema definitions that include ProcessingMode enum
from app.services.entry_processing import get_entry_processing_service

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


@router.post("/process/{entry_id}", response_model=EntryResponse)
async def process_entry(
    entry_id: int = Path(..., description="Entry ID"),
    process_request: EntryProcessRequest = ...
):
    """Process an existing entry with specified mode (enhanced or structured)"""
    try:
        # Get existing entry
        entry = await EntryRepository.get_by_id(entry_id)
        
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        # Get processing service
        processing_service = await get_entry_processing_service()
        
        # Process the entry
        result = await processing_service.process_entry(
            raw_text=entry.raw_text,
            mode=process_request.mode,
            existing_entry=entry
        )
        
        # Update entry based on processing mode
        if process_request.mode == ProcessingMode.ENHANCED:
            entry.enhanced_text = result["processed_text"]
        elif process_request.mode == ProcessingMode.STRUCTURED:
            entry.structured_summary = result["processed_text"]
        
        # Update processing metadata
        entry.processing_metadata = result["processing_metadata"]
        entry.word_count = result["word_count"]
        entry.mode = process_request.mode.value
        
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
        raise HTTPException(status_code=500, detail=f"Failed to process entry: {str(e)}")


@router.get("/stats/count", response_model=dict)
async def get_entry_count():
    """Get total count of entries"""
    try:
        count = await EntryRepository.count()
        return {"total_entries": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entry count: {str(e)}")
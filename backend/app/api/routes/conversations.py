"""
Conversation API endpoints for Talk to Your Diary feature.

This module provides endpoints for:
- Creating and managing conversation sessions
- Retrieving conversation history and transcriptions
- Conversation statistics and analytics
"""

import logging
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.schemas import SuccessResponse, ErrorResponse
from app.db.repositories.conversation_repository import ConversationRepository
from app.models.conversation import Conversation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


# Request Models
class ConversationCreateRequest(BaseModel):
    """Request model for creating a new conversation."""
    conversation_type: str = Field(..., pattern="^(call|chat)$", description="Type of conversation: 'call' or 'chat'")
    transcription: str = Field(..., min_length=1, max_length=50000, description="Complete conversation transcription")
    duration: int = Field(0, ge=0, description="Conversation duration in seconds")
    message_count: int = Field(0, ge=0, description="Number of messages in the conversation")
    search_queries_used: Optional[List[str]] = Field(None, description="Search queries used during conversation")


class ConversationUpdateRequest(BaseModel):
    """Request model for updating a conversation."""
    transcription: Optional[str] = Field(None, min_length=1, max_length=50000, description="Updated transcription")
    duration: Optional[int] = Field(None, ge=0, description="Updated duration in seconds")
    message_count: Optional[int] = Field(None, ge=0, description="Updated message count")
    search_queries_used: Optional[List[str]] = Field(None, description="Updated search queries")


# Response Models
class ConversationResponse(BaseModel):
    """Response model for conversation data."""
    id: int = Field(..., description="Conversation ID")
    timestamp: str = Field(..., description="Conversation timestamp")
    duration: int = Field(..., description="Duration in seconds")
    transcription: str = Field(..., description="Complete transcription")
    conversation_type: str = Field(..., description="Type: 'call' or 'chat'")
    message_count: int = Field(..., description="Number of messages")
    search_queries_used: Optional[List[str]] = Field(None, description="Search queries used")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


class ConversationStatsResponse(BaseModel):
    """Response model for conversation statistics."""
    total_conversations: int = Field(..., description="Total number of conversations")
    call_conversations: int = Field(..., description="Number of call conversations")
    chat_conversations: int = Field(..., description="Number of chat conversations")
    total_duration: int = Field(..., description="Total duration in seconds")
    total_messages: int = Field(..., description="Total message count")
    average_duration: float = Field(..., description="Average conversation duration")
    average_messages: float = Field(..., description="Average messages per conversation")
    most_recent: Optional[str] = Field(None, description="Most recent conversation timestamp")


@router.post("", response_model=SuccessResponse[ConversationResponse])
async def create_conversation(request: ConversationCreateRequest):
    """
    Create a new conversation record.
    
    Args:
        request: Conversation creation data
        
    Returns:
        Created conversation with assigned ID
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        # Create conversation object
        conversation = Conversation(
            timestamp=datetime.now(),
            duration=request.duration,
            transcription=request.transcription,
            conversation_type=request.conversation_type,
            message_count=request.message_count,
            search_queries_used=request.search_queries_used or [],
            created_at=datetime.now()
        )
        
        # Save to database
        created_conversation = await ConversationRepository.create(conversation)
        
        # Convert to response format
        response_data = ConversationResponse(
            id=created_conversation.id,
            timestamp=created_conversation.timestamp.isoformat(),
            duration=created_conversation.duration,
            transcription=created_conversation.transcription,
            conversation_type=created_conversation.conversation_type,
            message_count=created_conversation.message_count,
            search_queries_used=created_conversation.search_queries_used,
            created_at=created_conversation.created_at.isoformat(),
            updated_at=created_conversation.updated_at.isoformat() if created_conversation.updated_at else None
        )
        
        return SuccessResponse(
            success=True,
            message=f"Conversation created successfully",
            data=response_data
        )
        
    except ValueError as e:
        logger.error(f"Invalid conversation data: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid conversation data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create conversation: {str(e)}"
        )


@router.get("", response_model=SuccessResponse[List[ConversationResponse]])
async def get_conversations(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of conversations to return"),
    offset: int = Query(0, ge=0, description="Number of conversations to skip"),
    conversation_type: Optional[str] = Query(None, regex="^(call|chat)$", description="Filter by conversation type")
):
    """
    Retrieve conversations with pagination and filtering.
    
    Args:
        limit: Maximum number of results
        offset: Number of results to skip
        conversation_type: Optional filter by type
        
    Returns:
        List of conversations matching criteria
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # Retrieve conversations from database
        conversations = await ConversationRepository.get_all(
            limit=limit,
            offset=offset,
            conversation_type=conversation_type
        )
        
        # Convert to response format
        response_data = []
        for conv in conversations:
            response_data.append(ConversationResponse(
                id=conv.id,
                timestamp=conv.timestamp.isoformat(),
                duration=conv.duration,
                transcription=conv.transcription,
                conversation_type=conv.conversation_type,
                message_count=conv.message_count,
                search_queries_used=conv.search_queries_used,
                created_at=conv.created_at.isoformat(),
                updated_at=conv.updated_at.isoformat() if conv.updated_at else None
            ))
        
        return SuccessResponse(
            success=True,
            message=f"Retrieved {len(response_data)} conversations",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve conversations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve conversations: {str(e)}"
        )


@router.get("/{conversation_id}", response_model=SuccessResponse[ConversationResponse])
async def get_conversation(conversation_id: int):
    """
    Retrieve a specific conversation by ID.
    
    Args:
        conversation_id: Conversation ID to retrieve
        
    Returns:
        Conversation data
        
    Raises:
        HTTPException: If conversation not found or retrieval fails
    """
    try:
        conversation = await ConversationRepository.get_by_id(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation with ID {conversation_id} not found"
            )
        
        response_data = ConversationResponse(
            id=conversation.id,
            timestamp=conversation.timestamp.isoformat(),
            duration=conversation.duration,
            transcription=conversation.transcription,
            conversation_type=conversation.conversation_type,
            message_count=conversation.message_count,
            search_queries_used=conversation.search_queries_used,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat() if conversation.updated_at else None
        )
        
        return SuccessResponse(
            success=True,
            message="Conversation retrieved successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve conversation: {str(e)}"
        )


@router.put("/{conversation_id}", response_model=SuccessResponse[ConversationResponse])
async def update_conversation(conversation_id: int, request: ConversationUpdateRequest):
    """
    Update a conversation's details.
    
    Args:
        conversation_id: Conversation ID to update
        request: Updated conversation data
        
    Returns:
        Updated conversation data
        
    Raises:
        HTTPException: If conversation not found or update fails
    """
    try:
        # Check if conversation exists
        existing_conversation = await ConversationRepository.get_by_id(conversation_id)
        if not existing_conversation:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation with ID {conversation_id} not found"
            )
        
        # Update conversation
        updated_conversation = await ConversationRepository.update(
            conversation_id=conversation_id,
            transcription=request.transcription,
            duration=request.duration,
            message_count=request.message_count,
            search_queries_used=request.search_queries_used
        )
        
        response_data = ConversationResponse(
            id=updated_conversation.id,
            timestamp=updated_conversation.timestamp.isoformat(),
            duration=updated_conversation.duration,
            transcription=updated_conversation.transcription,
            conversation_type=updated_conversation.conversation_type,
            message_count=updated_conversation.message_count,
            search_queries_used=updated_conversation.search_queries_used,
            created_at=updated_conversation.created_at.isoformat(),
            updated_at=updated_conversation.updated_at.isoformat() if updated_conversation.updated_at else None
        )
        
        return SuccessResponse(
            success=True,
            message="Conversation updated successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update conversation: {str(e)}"
        )


@router.delete("/{conversation_id}", response_model=SuccessResponse[dict])
async def delete_conversation(conversation_id: int):
    """
    Delete a conversation.
    
    Args:
        conversation_id: Conversation ID to delete
        
    Returns:
        Success confirmation
        
    Raises:
        HTTPException: If conversation not found or deletion fails
    """
    try:
        # Check if conversation exists
        existing_conversation = await ConversationRepository.get_by_id(conversation_id)
        if not existing_conversation:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation with ID {conversation_id} not found"
            )
        
        # Delete conversation
        success = await ConversationRepository.delete(conversation_id)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete conversation"
            )
        
        return SuccessResponse(
            success=True,
            message=f"Conversation {conversation_id} deleted successfully",
            data={
                "conversation_id": conversation_id,
                "deleted": True
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete conversation: {str(e)}"
        )


@router.get("/stats/summary", response_model=SuccessResponse[ConversationStatsResponse])
async def get_conversation_statistics():
    """
    Get conversation statistics and analytics.
    
    Returns:
        Comprehensive conversation statistics
        
    Raises:
        HTTPException: If statistics retrieval fails
    """
    try:
        stats = await ConversationRepository.get_statistics()
        
        response_data = ConversationStatsResponse(
            total_conversations=stats.get("total_conversations", 0),
            call_conversations=stats.get("call_conversations", 0),
            chat_conversations=stats.get("chat_conversations", 0),
            total_duration=stats.get("total_duration", 0),
            total_messages=stats.get("total_messages", 0),
            average_duration=stats.get("average_duration", 0.0),
            average_messages=stats.get("average_messages", 0.0),
            most_recent=stats.get("most_recent")
        )
        
        return SuccessResponse(
            success=True,
            message="Conversation statistics retrieved successfully",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve conversation statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )
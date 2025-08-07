"""
Diary Chat API endpoints for Talk to Your Diary feature.

This module provides conversational AI endpoints that allow users to interact 
with their diary entries through natural language.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from app.api.schemas import SuccessResponse, ErrorResponse
from app.services.diary_chat_service import get_diary_chat_service
from app.db.repositories.conversation_repository import ConversationRepository
from app.models.conversation import Conversation
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diary", tags=["diary-chat"])


class DiaryChatRequest(BaseModel):
    """Request model for diary chat."""
    message: str = Field(..., min_length=1, max_length=2000, description="User's message to the diary")
    conversation_history: Optional[List[Dict[str, str]]] = Field(None, description="Previous conversation messages")
    conversation_id: Optional[int] = Field(None, description="Optional conversation ID to continue existing conversation")


class DiaryChatResponse(BaseModel):
    """Response model for diary chat."""
    response: str = Field(..., description="Echo's response to the user")
    tool_calls_made: List[Dict[str, Any]] = Field(default_factory=list, description="Search tools that were used")
    search_queries_used: List[str] = Field(default_factory=list, description="Queries used to search diary")
    search_feedback: Optional[str] = Field(None, description="Feedback message about search process")
    tool_feedback: Optional[str] = Field(None, description="Tool-specific feedback message")
    processing_phases: List[Dict[str, Any]] = Field(default_factory=list, description="Processing phases for frontend status")
    conversation_id: Optional[int] = Field(None, description="ID of the conversation if saved")


class SearchFeedbackRequest(BaseModel):
    """Request model for search feedback."""
    pass


@router.post("/chat", response_model=SuccessResponse[DiaryChatResponse])
async def chat_with_diary(
    request: DiaryChatRequest,
    background_tasks: BackgroundTasks
) -> SuccessResponse[DiaryChatResponse]:
    """
    Chat with your diary using natural language.
    
    Echo will search through your diary entries to answer questions about your
    past experiences, thoughts, and patterns.
    
    Args:
        request: Chat request with message and optional conversation history
        background_tasks: FastAPI background tasks for async operations
        
    Returns:
        Response with Echo's message and search information
    """
    try:
        # Get diary chat service
        chat_service = get_diary_chat_service()
        
        logger.info(f"Processing diary chat message: '{request.message[:50]}...'")
        
        # Process the message with LLM and tools
        chat_response = await chat_service.process_message(
            message=request.message,
            conversation_history=request.conversation_history,
            background_tasks=background_tasks
        )
        
        # Prepare response data
        response_data = DiaryChatResponse(
            response=chat_response.get("response", ""),
            tool_calls_made=chat_response.get("tool_calls_made", []),
            search_queries_used=chat_response.get("search_queries_used", []),
            search_feedback=None,  # Will be set by frontend via separate endpoint
            tool_feedback=chat_response.get("tool_feedback"),
            processing_phases=chat_response.get("processing_phases", []),
            conversation_id=request.conversation_id
        )
        
        # Save conversation in background if conversation_id is provided
        if request.conversation_id:
            background_tasks.add_task(
                _update_conversation_with_chat,
                request.conversation_id,
                request.message,
                response_data.response,
                response_data.search_queries_used
            )
        
        logger.info(f"Successfully processed diary chat. Tools used: {len(response_data.tool_calls_made)}")
        
        return SuccessResponse(
            message="Chat processed successfully",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Error in diary chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process diary chat: {str(e)}"
        )


@router.get("/search-feedback", response_model=SuccessResponse[str])
async def get_search_feedback() -> SuccessResponse[str]:
    """
    Get a random search feedback message to display while processing.
    
    Returns friendly messages like "Checking diary..." or "Reading your thoughts..."
    to show users that Echo is actively searching their entries.
    
    Returns:
        Random search feedback message
    """
    try:
        chat_service = get_diary_chat_service()
        feedback = chat_service.get_random_search_feedback()
        
        return SuccessResponse(
            message="Search feedback generated",
            data=feedback
        )
        
    except Exception as e:
        logger.error(f"Error getting search feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get search feedback: {str(e)}"
        )


@router.get("/greeting", response_model=SuccessResponse[str])
async def get_greeting() -> SuccessResponse[str]:
    """
    Get a random greeting message for modal initialization.
    
    Returns one of 10 friendly greeting variants to welcome users
    and explain available interaction methods (type or voice).
    
    Returns:
        Random greeting message from Echo
    """
    try:
        chat_service = get_diary_chat_service()
        greeting = chat_service.get_random_greeting()
        
        return SuccessResponse(
            message="Greeting generated",
            data=greeting
        )
        
    except Exception as e:
        logger.error(f"Error getting greeting: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get greeting: {str(e)}"
        )


async def _update_conversation_with_chat(
    conversation_id: int,
    user_message: str,
    echo_response: str,
    search_queries: List[str]
):
    """
    Background task to update conversation with new chat messages.
    
    Args:
        conversation_id: ID of conversation to update
        user_message: User's message
        echo_response: Echo's response
        search_queries: Queries used in search
    """
    try:
        repo = ConversationRepository()
        
        # Get existing conversation
        conversation = await repo.get_by_id(conversation_id)
        if not conversation:
            logger.warning(f"Conversation {conversation_id} not found for chat update")
            return
        
        # Update conversation data
        conversation.message_count += 2  # User message + Echo response
        conversation.transcription += f"\n\nUser: {user_message}\nEcho: {echo_response}"
        
        # Update search queries used
        if conversation.search_queries_used:
            existing_queries = conversation.search_queries_used
        else:
            existing_queries = []
        
        # Add new queries (avoid duplicates)
        for query in search_queries:
            if query not in existing_queries:
                existing_queries.append(query)
        
        conversation.search_queries_used = existing_queries
        conversation.updated_at = datetime.now()
        
        # Save updated conversation
        await repo.update(conversation)
        
        logger.info(f"Updated conversation {conversation_id} with chat data")
        
    except Exception as e:
        logger.error(f"Error updating conversation {conversation_id} with chat: {e}")
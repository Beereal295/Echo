"""
Diary Chat Service for Talk to Your Diary feature using LangChain.

This service handles:
- LangChain ChatOllama integration with tool calling
- Date-aware diary search tool execution  
- Conversation context management
- System date awareness for the LLM
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
import re

from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from app.db.repositories.entry_repository import EntryRepository
from app.db.repositories.preferences_repository import PreferencesRepository
from app.services.embedding_service import get_embedding_service
from app.core.config import settings

logger = logging.getLogger(__name__)


def strip_thinking_block(response_text: str) -> str:
    """Strip thinking blocks from LLM response to get clean text."""
    if not response_text:
        return response_text
    
    # Find the end of the thinking block
    think_end = response_text.find('</think>')
    if think_end != -1:
        # Return everything after </think> tag, stripped of leading whitespace
        clean_text = response_text[think_end + len('</think>'):].strip()
        return clean_text
    
    # If no thinking block found, return original text
    return response_text

@tool
async def search_diary_entries(query: str, limit: int = 10) -> Dict[str, Any]:
    """Search user's diary entries by content using semantic search.
    
    args:
        query: Text query to search for (1-1000 characters)
        limit: Maximum number of results to return (1-20)
        
    Returns:
        Search results with entries and metadata
    """
    try:
        logger.info(f"Searching diary entries: query='{query}', limit={limit}")
        
        # Validate inputs
        if not query or len(query.strip()) == 0:
            return {"success": False, "error": "Query cannot be empty"}
        
        if limit < 1 or limit > 20:
            limit = 10
            
        query = query.strip()[:1000]  # Limit query length
        
        # Get embedding service and generate query embedding
        embedding_service = get_embedding_service()
        query_embedding = await embedding_service.generate_embedding(
            text=query,
            normalize=True,
            is_query=True  # Mark as query for BGE formatting
        )
        
        # Get all entries with embeddings (no date filtering)
        entries_with_embeddings = await EntryRepository.get_entries_with_embeddings(
            limit=1000  # Get a large batch for comprehensive search
        )
        
        if not entries_with_embeddings:
            return {
                "success": True,
                "results": [],
                "count": 0,
                "query": query,
                "message": "No entries with embeddings found"
            }
        
        # Extract embeddings and metadata
        candidate_embeddings = []
        entry_metadata = []
        
        for entry in entries_with_embeddings:
            if entry.embeddings and len(entry.embeddings) > 0:
                candidate_embeddings.append(entry.embeddings)
                entry_metadata.append(entry)
        
        if not candidate_embeddings:
            return {
                "success": True,
                "results": [],
                "count": 0,
                "query": query,
                "message": "No valid embeddings found"
            }
        
        # Perform similarity search
        similar_indices = embedding_service.search_similar_embeddings(
            query_embedding=query_embedding,
            candidate_embeddings=candidate_embeddings,
            top_k=limit,
            similarity_threshold=0.3
        )
        
        # Format results
        results = []
        for index, similarity in similar_indices:
            entry = entry_metadata[index]
            
            # Include full entry data with mood_tags for LLM analysis
            result = {
                "entry_id": entry.id,
                "content": entry.raw_text or "",
                "enhanced_text": entry.enhanced_text or "",
                "structured_summary": entry.structured_summary or "",
                "timestamp": entry.timestamp.isoformat(),
                "mood_tags": entry.mood_tags or [],
                "mode": entry.mode,
                "similarity": similarity,
                "word_count": entry.word_count
            }
            results.append(result)
        
        return {
            "success": True,
            "results": results,
            "count": len(results),
            "query": query,
            "total_searchable_entries": len(candidate_embeddings)
        }
        
    except Exception as e:
        logger.error(f"Error in search_diary_entries: {e}")
        return {"success": False, "error": str(e)}


@tool 
async def get_entries_by_date(date_filter: str, limit: int = 100) -> Dict[str, Any]:
    """Get diary entries filtered by specific dates or date ranges.
    
    Use this tool when the user asks about entries from specific dates like:
    - "yesterday", "today", "last week"
    - "last Saturday", "this Monday", "two days ago"
    - "January 15th", "last month", "this year"
    
    args:
        date_filter: Natural language date filter (e.g., "yesterday", "last Saturday", "this week")
        limit: Maximum number of results to return (100)
        
    Returns:
        Entries matching the date filter with full content and mood_tags
    """
    try:
        logger.info(f"Getting entries by date: filter='{date_filter}', limit={limit}")
        
        # Get current date for calculations
        today = date.today()
        now = datetime.now()
        
        # Parse date filter and calculate date range
        start_date = None
        end_date = None
        
        date_filter_lower = date_filter.lower().strip()
        
        if date_filter_lower in ["today"]:
            start_date = today
            end_date = today
        elif date_filter_lower in ["yesterday"]:
            yesterday = today - timedelta(days=1)
            start_date = yesterday
            end_date = yesterday
        elif date_filter_lower in ["last week", "this week"]:
            # Get start of current week (Monday)
            days_since_monday = today.weekday()
            if date_filter_lower == "this week":
                start_date = today - timedelta(days=days_since_monday)
                end_date = today
            else:  # last week
                start_date = today - timedelta(days=days_since_monday + 7)
                end_date = today - timedelta(days=days_since_monday + 1)
        elif date_filter_lower in ["last month", "this month"]:
            if date_filter_lower == "this month":
                start_date = today.replace(day=1)
                end_date = today
            else:  # last month
                first_this_month = today.replace(day=1)
                end_date = first_this_month - timedelta(days=1)
                start_date = end_date.replace(day=1)
        elif "days ago" in date_filter_lower:
            # Parse "X days ago"
            match = re.search(r'(\d+)\s+days?\s+ago', date_filter_lower)
            if match:
                days_ago = int(match.group(1))
                target_date = today - timedelta(days=days_ago)
                start_date = target_date
                end_date = target_date
        elif any(day in date_filter_lower for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
            # Parse "last Saturday", "this Monday", etc.
            days_of_week = {
                "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                "friday": 4, "saturday": 5, "sunday": 6
            }
            
            for day_name, day_num in days_of_week.items():
                if day_name in date_filter_lower:
                    current_weekday = today.weekday()
                    
                    if "last" in date_filter_lower:
                        # Get last occurrence of this weekday
                        days_back = (current_weekday - day_num) % 7
                        if days_back == 0:  # If it's the same day, go back a week
                            days_back = 7
                        target_date = today - timedelta(days=days_back)
                    else:  # "this" or no qualifier
                        # Get this week's occurrence
                        days_forward = (day_num - current_weekday) % 7
                        target_date = today + timedelta(days=days_forward)
                        
                        # If it's in the future, get last week's occurrence
                        if target_date > today:
                            target_date = target_date - timedelta(days=7)
                    
                    start_date = target_date
                    end_date = target_date
                    break
        
        # If we couldn't parse the date filter, return last 7 days as fallback
        if start_date is None:
            logger.warning(f"Could not parse date filter '{date_filter}', using last 7 days")
            start_date = today - timedelta(days=7)
            end_date = today
        
        # Convert to datetime for database query
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        logger.info(f"Date range: {start_datetime} to {end_datetime}")
        
        # Get entries with embeddings in the date range
        entries = await EntryRepository.get_entries_with_embeddings(
            limit=limit,
            start_date=start_datetime.isoformat(),
            end_date=end_datetime.isoformat()
        )
        
        # Format results with full content and mood_tags
        results = []
        for entry in entries:
            result = {
                "entry_id": entry.id,
                "content": entry.raw_text or "",
                "enhanced_text": entry.enhanced_text or "",
                "structured_summary": entry.structured_summary or "",
                "timestamp": entry.timestamp.isoformat(),
                "mood_tags": entry.mood_tags or [],
                "mode": entry.mode,
                "word_count": entry.word_count
            }
            results.append(result)
        
        return {
            "success": True,
            "results": results,
            "count": len(results),
            "date_filter": date_filter,
            "date_range": {
                "start_date": start_datetime.isoformat(),
                "end_date": end_datetime.isoformat()
            },
            "message": f"Found {len(results)} entries for {date_filter}"
        }
        
    except Exception as e:
        logger.error(f"Error in get_entries_by_date: {e}")
        return {"success": False, "error": str(e)}


class DiaryChatService:
    """Service for diary conversations using LangChain ChatOllama with tool calling."""
    
    def __init__(self):
        """Initialize the diary chat service with LangChain ChatOllama."""
        # Will be initialized with preferences in async method
        self.llm = None
        self.llm_with_tools = None
        self._initialized = False
        
        self.search_feedback_messages = [
            "Checking diary...",
            "Reading your thoughts...",
            "Searching your memories...",
            "Looking through your entries...",
            "Finding relevant moments...",
            "Exploring your past entries...",
            "Scanning your journal...",
            "Reviewing your thoughts..."
        ]
        
        # AI greeting variants for modal initialization
        self.greeting_variants = [
            "Hi there! I'm Echo, your diary companion. You can type your thoughts or use the voice button to talk with me. What's on your mind today?",
            "Hello! Echo here, ready to help you explore your diary. Feel free to type or speak - I'm listening. How can I assist you?",
            "Hey! I'm Echo, and I'm here to chat about your journal entries. You can write or use voice - whatever feels comfortable. What would you like to discuss?",
            "Hi! It's Echo, your personal diary AI. Type away or hit the mic button to speak with me. What are you curious about from your entries?",
            "Hello there! I'm Echo, ready to dive into your diary with you. Use text or voice - I'm here either way. What's something you'd like to explore?",
            "Hey! Echo at your service, ready to chat about your journal. Type your questions or speak them aloud - I'm all ears. What shall we talk about?",
            "Hi! I'm Echo, your diary conversation partner. Whether you type or talk, I'm here to help. What memories or thoughts would you like to revisit?",
            "Hello! Echo here, excited to explore your diary together. Use the keyboard or microphone - both work great. What's something interesting you'd like to find?",
            "Hey there! I'm Echo, and I love helping you discover insights from your entries. Type or speak your thoughts - I'm ready. What's on your agenda today?",
            "Hi! It's Echo, your journal AI companion. Feel free to type or use voice input - whatever suits you best. What would you like to uncover from your diary?"
        ]
    
    async def _ensure_initialized(self):
        """Ensure the service is initialized with current preferences."""
        if self._initialized:
            return
        
        try:
            # Load Talk to Your Diary specific preferences from database
            model_name = await PreferencesRepository.get_value('talk_to_diary_model', 'qwen3:8b')
            temperature = await PreferencesRepository.get_value('talk_to_diary_temperature', 0.2)  
            base_url = await PreferencesRepository.get_value('ollama_url', 'http://localhost:11434')
            num_ctx = await PreferencesRepository.get_value('talk_to_diary_context_window', 8192)
            
            logger.info(f"Initializing DiaryChatService with model: {model_name}, temp: {temperature}, ctx: {num_ctx}")
            
            # Initialize ChatOllama with preferences  
            self.llm = ChatOllama(
                model=model_name,
                base_url=base_url,
                temperature=float(temperature),
                num_ctx=int(num_ctx)
            )
            
            logger.info(f"Initialized LLM with model: {model_name}")
            
            # Bind tools to the LLM
            self.llm_with_tools = self.llm.bind_tools([search_diary_entries, get_entries_by_date])
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize DiaryChatService: {e}")
            # Fallback to defaults
            self.llm = ChatOllama(
                model=settings.OLLAMA_DEFAULT_MODEL,
                base_url='http://localhost:11434',
                temperature=0.1,
                num_ctx=4096
            )
            self.llm_with_tools = self.llm.bind_tools([search_diary_entries, get_entries_by_date])
            self._initialized = True
    
    async def process_message(
        self, 
        message: str, 
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message with LangChain tool calling.
        
        Args:
            message: User's message
            conversation_history: Previous conversation messages
            
        Returns:
            Response with message, tool calls used, and search feedback
        """
        try:
            # Ensure service is initialized with current preferences
            await self._ensure_initialized()
            
            logger.info(f"Processing diary chat message: '{message[:50]}...'")
            
            # Build message history for LangChain with system date awareness
            today = date.today()
            messages = [
                SystemMessage(content=f"""You are Echo, a diary companion. Today is {today.strftime('%A, %B %d, %Y')}.

When users ask about their diary entries, use the available tools:
- search_diary_entries: for content-based searches like "hiking", "work", "friends"
- get_entries_by_date: for recent entries like "yesterday", "last few days"

Use tools to find relevant entries.""")
            ]
            
            # Add conversation history
            if conversation_history:
                for turn in conversation_history[-5:]:  # Last 5 turns for context
                    role = turn.get("role", "user")
                    content = turn.get("content", "")
                    if role == "user":
                        messages.append(HumanMessage(content=content))
                    elif role == "assistant":
                        messages.append(AIMessage(content=content))
            
            # Add current message
            messages.append(HumanMessage(content=message))
            
            # Get response from LLM with tools
            response = await self.llm_with_tools.ainvoke(messages)
            
            # Debug logging
            logger.info(f"LLM Response type: {type(response)}")
            logger.info(f"Response content: {response.content[:200]}...")
            logger.info(f"Response tool_calls: {response.tool_calls}")
            
            # Process tool calls if any
            tool_calls_made = []
            search_queries_used = []
            
            if response.tool_calls:
                logger.info(f"Tool calls detected: {len(response.tool_calls)}")
                
                # Execute tool calls
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    
                    logger.info(f"Executing {tool_name} with args: {tool_args}")
                    
                    if tool_name == "search_diary_entries":
                        tool_result = await search_diary_entries.ainvoke(tool_args)
                    elif tool_name == "get_entries_by_date":
                        tool_result = await get_entries_by_date.ainvoke(tool_args)
                    else:
                        logger.warning(f"Unknown tool: {tool_name}")
                        continue
                    
                    tool_calls_made.append({
                        "tool": tool_name,
                        "arguments": tool_args,
                        "result": tool_result
                    })
                    
                    # Track search queries
                    if tool_name == "search_diary_entries":
                        query = tool_args.get("query", "")
                        if query:
                            search_queries_used.append(query)
                    elif tool_name == "get_entries_by_date":
                        date_filter = tool_args.get("date_filter", "")
                        if date_filter:
                            search_queries_used.append(f"Date: {date_filter}")
            
            # If tools were executed, get final response with tool results (like test script)
            if tool_calls_made:
                # Add the tool call message to conversation
                messages.append(response)
                
                # Add tool results as ToolMessages
                for i, tool_call in enumerate(tool_calls_made):
                    tool_call_id = response.tool_calls[i]["id"] if i < len(response.tool_calls) else "unknown"
                    messages.append(ToolMessage(
                        content=str(tool_call["result"]),
                        tool_call_id=tool_call_id
                    ))
                
                # Add focused system prompt for response generation
                response_messages = [
                    SystemMessage(content="You are Echo. Look for tool results containing diary entry data. Analyze those diary entries and thoughtfully reply as if you are talking to the user naturally using 'you' and 'your'."),
                    *messages[1:]  # Skip original system message, keep user message, AI response, and tool results
                ]
                
                # Get final response using base LLM (no tools needed)
                final_response_msg = await self.llm.ainvoke(response_messages)
                final_response = strip_thinking_block(final_response_msg.content)
            else:
                final_response = strip_thinking_block(response.content)
            
            # Fallback if response is empty
            if not final_response or final_response.strip() == "":
                final_response = "Hello! I'm Echo, your diary companion. I'm here to help you explore your thoughts and memories. What would you like to talk about today?"
                logger.warning("Used fallback response due to empty model response")
            
            return {
                "response": final_response,
                "tool_calls_made": tool_calls_made,
                "search_queries_used": search_queries_used
            }
            
        except Exception as e:
            logger.error(f"Error processing diary chat message: {e}", exc_info=True)
            return {
                "response": "I'm sorry, I encountered an error while processing your message. Please try again.",
                "tool_calls_made": [],
                "search_queries_used": [],
                "error": str(e)
            }
    
    def get_random_search_feedback(self) -> str:
        """Get a random search feedback message."""
        import random
        return random.choice(self.search_feedback_messages)
    
    def get_random_greeting(self) -> str:
        """Get a random greeting message for modal initialization."""
        import random
        return random.choice(self.greeting_variants)


# Global diary chat service instance
_diary_chat_service: Optional[DiaryChatService] = None


def get_diary_chat_service() -> DiaryChatService:
    """Get the global diary chat service instance."""
    global _diary_chat_service
    if _diary_chat_service is None:
        _diary_chat_service = DiaryChatService()
    return _diary_chat_service
#!/usr/bin/env python3
"""
Test script to debug LangChain tool binding issues.
This script tests both with and without tool binding using actual APIs.
"""

import asyncio
import sys
import os
import logging
from datetime import date, datetime, timedelta

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Initialize the database connection to use actual echo.db
from app.db.database import db, init_db

from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

# Import our actual services
from app.db.repositories.entry_repository import EntryRepository
from app.services.embedding_service import get_embedding_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@tool
async def search_diary_simple(query: str) -> dict:
    """Simple search tool for testing - searches diary entries by content."""
    try:
        logger.info(f"🔍 TOOL EXECUTED: search_diary_simple with query='{query}'")
        
        # Get embedding service and generate query embedding
        embedding_service = get_embedding_service()
        query_embedding = await embedding_service.generate_embedding(
            text=query,
            normalize=True,
            is_query=True
        )
        
        # Get entries with embeddings
        entries = await EntryRepository.get_entries_with_embeddings(limit=50)
        
        if not entries:
            return {"success": True, "count": 0, "message": "No entries found"}
        
        # Extract embeddings and metadata
        candidate_embeddings = []
        entry_metadata = []
        
        for entry in entries:
            if entry.embeddings and len(entry.embeddings) > 0:
                candidate_embeddings.append(entry.embeddings)
                entry_metadata.append(entry)
        
        if not candidate_embeddings:
            return {"success": True, "count": 0, "message": "No valid embeddings found"}
        
        # Perform similarity search
        similar_indices = embedding_service.search_similar_embeddings(
            query_embedding=query_embedding,
            candidate_embeddings=candidate_embeddings,
            top_k=3,
            similarity_threshold=0.3
        )
        
        # Format results
        results = []
        for index, similarity in similar_indices:
            entry = entry_metadata[index]
            results.append({
                "entry_id": entry.id,
                "content_preview": entry.raw_text[:100] + "..." if entry.raw_text else "",
                "timestamp": entry.timestamp.strftime("%Y-%m-%d"),
                "similarity": similarity
            })
        
        logger.info(f"✅ TOOL RESULT: Found {len(results)} entries")
        return {
            "success": True,
            "count": len(results),
            "results": results,
            "query": query
        }
        
    except Exception as e:
        logger.error(f"❌ TOOL ERROR: {e}")
        return {"success": False, "error": str(e)}


@tool
async def get_recent_entries(days_back: int = 1) -> dict:
    """Get entries from recent days."""
    try:
        logger.info(f"🔍 TOOL EXECUTED: get_recent_entries with days_back={days_back}")
        
        # Calculate date range
        today = date.today()
        start_date = today - timedelta(days=days_back)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(today, datetime.max.time())
        
        # Get entries in date range
        entries = await EntryRepository.get_entries_with_embeddings(
            limit=20,
            start_date=start_datetime.isoformat(),
            end_date=end_datetime.isoformat()
        )
        
        results = []
        for entry in entries:
            results.append({
                "entry_id": entry.id,
                "content_preview": entry.raw_text[:100] + "..." if entry.raw_text else "",
                "timestamp": entry.timestamp.strftime("%Y-%m-%d %H:%M"),
                "mood_tags": entry.mood_tags or []
            })
        
        logger.info(f"✅ TOOL RESULT: Found {len(results)} entries from last {days_back} days")
        return {
            "success": True,
            "count": len(results),
            "results": results,
            "date_range": f"Last {days_back} days"
        }
        
    except Exception as e:
        logger.error(f"❌ TOOL ERROR: {e}")
        return {"success": False, "error": str(e)}


async def test_without_tools():
    """Test LLM without tool binding."""
    print("\n" + "="*60)
    print("🧪 TEST 1: LLM WITHOUT TOOLS")
    print("="*60)
    
    try:
        llm = ChatOllama(
            model="mistral:latest",
            base_url="http://localhost:11434",
            temperature=0.1,
            num_ctx=2048
        )
        
        message = "Hello, can you tell me when I went hiking?"
        
        response = await llm.ainvoke([HumanMessage(content=message)])
        
        print(f"📤 User: {message}")
        print(f"🤖 LLM Response: {response.content}")
        print(f"🔧 Tool calls: {getattr(response, 'tool_calls', 'None')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in test without tools: {e}")
        return False


async def test_with_tools():
    """Test LLM with tool binding."""
    print("\n" + "="*60)
    print("🧪 TEST 2: LLM WITH TOOLS")
    print("="*60)
    
    try:
        llm = ChatOllama(
            model="mistral:latest",
            base_url="http://localhost:11434",
            temperature=0.1,
            num_ctx=2048
        )
        
        # Bind tools
        llm_with_tools = llm.bind_tools([search_diary_simple, get_recent_entries])
        
        today = date.today()
        system_msg = SystemMessage(content=f"""You are Echo, a diary companion. Today is {today.strftime('%A, %B %d, %Y')}.

When users ask about their diary entries, use the available tools:
- search_diary_simple: for content-based searches like "hiking", "work", "friends"
- get_recent_entries: for recent entries like "yesterday", "last few days"

Use tools to find relevant entries, then summarize the results naturally.""")
        
        # Test queries
        test_queries = [
            "When did I go hiking?",
            "What did I write yesterday?",
            "Tell me about my recent diary entries",
            "Can you summarize all my entries from yesterday and tell me briefly how my day was?",
            "What were my moods like yesterday? How was I feeling emotionally?"
        ]
        
        for query in test_queries:
            print(f"\n📤 User: {query}")
            
            messages = [system_msg, HumanMessage(content=query)]
            response = await llm_with_tools.ainvoke(messages)
            
            print(f"🤖 LLM Response: {response.content}")
            print(f"🔧 Tool calls: {response.tool_calls}")
            
            # If there are tool calls, execute them and get final response
            if response.tool_calls:
                print(f"🚀 Executing {len(response.tool_calls)} tool calls...")
                
                messages.append(response)
                
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    
                    print(f"  🔧 Calling {tool_name} with args: {tool_args}")
                    
                    if tool_name == "search_diary_simple":
                        tool_result = await search_diary_simple.ainvoke(tool_args)
                    elif tool_name == "get_recent_entries":
                        tool_result = await get_recent_entries.ainvoke(tool_args)
                    else:
                        tool_result = {"success": False, "error": f"Unknown tool: {tool_name}"}
                    
                    print(f"  ✅ Tool result: {tool_result}")
                    
                    messages.append(ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call["id"]
                    ))
                
                # Get final response
                final_response = await llm.ainvoke(messages)
                print(f"🎯 Final Response: {final_response.content}")
            
            print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ Error in test with tools: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tool_execution_directly():
    """Test tool execution directly."""
    print("\n" + "="*60)
    print("🧪 TEST 3: DIRECT TOOL EXECUTION")
    print("="*60)
    
    try:
        # Test search tool directly
        print("Testing search_diary_simple directly...")
        result1 = await search_diary_simple.ainvoke({"query": "hiking"})
        print(f"✅ Search result: {result1}")
        
        # Test recent entries tool directly
        print("\nTesting get_recent_entries directly...")
        result2 = await get_recent_entries.ainvoke({"days_back": 2})
        print(f"✅ Recent entries result: {result2}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in direct tool execution: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting LangChain Tool Binding Tests")
    print(f"📅 Today: {date.today()}")
    
    # Initialize database connection to actual echo.db
    print(f"🗄️ Connecting to database: {db.db_path}")
    await db.connect()
    
    # Test database connection
    try:
        entry_count = await db.fetch_one("SELECT COUNT(*) as count FROM entries")
        print(f"📊 Found {entry_count['count']} entries in database")
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return
    
    # Test 1: Without tools
    success1 = await test_without_tools()
    
    # Test 2: With tools
    success2 = await test_with_tools()
    
    # Test 3: Direct tool execution
    success3 = await test_tool_execution_directly()
    
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    print(f"✅ Without tools: {'PASS' if success1 else 'FAIL'}")
    print(f"✅ With tools: {'PASS' if success2 else 'FAIL'}")
    print(f"✅ Direct tools: {'PASS' if success3 else 'FAIL'}")
    
    if success2:
        print("\n🎉 Tool binding appears to be working!")
    else:
        print("\n❌ Tool binding has issues - check the error output above")
    
    # Close database connection
    try:
        await db.disconnect()
        print("🔌 Database connection closed")
    except Exception as e:
        print(f"⚠️ Error closing database: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    finally:
        print("👋 Test script exiting...")
        # Force exit to ensure script doesn't hang
        import sys
        sys.exit(0)
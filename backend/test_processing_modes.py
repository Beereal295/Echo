#!/usr/bin/env python3
"""
Test script for Entry Processing Modes
Tests the three processing modes: Raw, Enhanced, and Structured
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, Any

import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_ENTRIES = [
    {
        "raw_text": "Um, so today was like really crazy you know? I went to the office and uh there was this meeting that went on forever and ever. My boss was talking about these new projects and stuff and I was just sitting there thinking about lunch. Then afterwards I had to finish this report that was due yesterday but I forgot about it. Anyway I managed to get it done somehow. Oh and I also called my mom she's doing well I think. Yeah so that's basically my day I guess.",
        "description": "Rambling speech with filler words"
    },
    {
        "raw_text": "I woke up at 7 AM feeling anxious about the presentation. Had coffee, reviewed my slides one more time. The presentation went well - got positive feedback from the team. Felt relieved afterwards. Went for a walk in the park during lunch. Weather was nice. Had dinner with Sarah, we talked about her new job. She seems excited about it. Watched a movie before bed. Overall a good day despite the morning anxiety.",
        "description": "Clear narrative with emotions and events"
    },
    {
        "raw_text": "Really struggling today you know? Everything feels overwhelming. Work is piling up and I can't seem to focus on anything. Had an argument with my partner about money again. These conversations never go well. I'm worried about our relationship sometimes. Maybe I should talk to someone about this. Also my back is hurting from sitting at the desk all day. Need to exercise more but I just don't have the energy. Feeling pretty low right now.",
        "description": "Emotional content with concerns"
    }
]


class ProcessingModeTester:
    """Test class for processing modes"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.created_entries = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        
    async def test_server_connection(self) -> bool:
        """Test if the server is running"""
        try:
            response = await self.client.get(f"{BASE_URL}/health/")
            if response.status_code == 200:
                console.print("✅ Server connection successful", style="green")
                return True
            else:
                console.print(f"❌ Server responded with status {response.status_code}", style="red")
                return False
        except Exception as e:
            console.print(f"❌ Failed to connect to server: {str(e)}", style="red")
            return False
    
    async def test_ollama_connection(self) -> bool:
        """Test Ollama service connection"""
        try:
            response = await self.client.post(f"{BASE_URL}/ollama/test")
            if response.status_code == 200:
                result = response.json()
                console.print("✅ Ollama connection successful", style="green")
                console.print(f"   Model: {result.get('model', 'Unknown')}")
                console.print(f"   Speed: {result.get('tokens_per_second', 'Unknown')} tokens/sec")
                return True
            else:
                console.print(f"❌ Ollama test failed with status {response.status_code}", style="red")
                return False
        except Exception as e:
            console.print(f"❌ Ollama connection failed: {str(e)}", style="red")
            return False
    
    async def create_test_entry(self, raw_text: str, description: str) -> Dict[str, Any]:
        """Create a raw entry for testing"""
        try:
            payload = {
                "raw_text": raw_text,
                "mode": "raw"
            }
            
            response = await self.client.post(f"{BASE_URL}/entries/", json=payload)
            
            if response.status_code == 201:
                entry = response.json()
                self.created_entries.append(entry["id"])
                console.print(f"✅ Created test entry (ID: {entry['id']}) - {description}", style="green")
                return entry
            else:
                console.print(f"❌ Failed to create entry: {response.status_code}", style="red")
                console.print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            console.print(f"❌ Error creating entry: {str(e)}", style="red")
            return None
    
    async def test_processing_mode(self, entry_id: int, mode: str, description: str) -> Dict[str, Any]:
        """Test a specific processing mode"""
        try:
            payload = {"mode": mode}
            
            with Progress(
                SpinnerColumn(),
                TextColumn(f"Processing with {mode.upper()} mode..."),
                console=console
            ) as progress:
                task = progress.add_task("processing", total=None)
                
                response = await self.client.post(
                    f"{BASE_URL}/entries/process/{entry_id}",
                    json=payload
                )
            
            if response.status_code == 200:
                result = response.json()
                console.print(f"✅ {mode.upper()} processing successful", style="green")
                
                # Extract processed text based on mode
                if mode == "enhanced":
                    processed_text = result.get("enhanced_text", "")
                elif mode == "structured":
                    processed_text = result.get("structured_summary", "")
                else:
                    processed_text = result.get("raw_text", "")
                
                # Display processing metadata
                metadata = result.get("processing_metadata", {})
                if metadata:
                    processing_time = metadata.get("processing_time_ms", 0)
                    model_used = metadata.get("model_used", "Unknown")
                    console.print(f"   Processing time: {processing_time:.2f}ms")
                    console.print(f"   Model used: {model_used}")
                
                return {
                    "success": True,
                    "processed_text": processed_text,
                    "metadata": metadata,
                    "word_count": result.get("word_count", 0)
                }
            else:
                console.print(f"❌ {mode.upper()} processing failed: {response.status_code}", style="red")
                console.print(f"   Response: {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            console.print(f"❌ Error in {mode.upper()} processing: {str(e)}", style="red")
            return {"success": False, "error": str(e)}
    
    async def display_comparison(self, raw_text: str, enhanced_result: Dict, structured_result: Dict):
        """Display comparison of processing results"""
        
        # Create comparison table
        table = Table(title="Processing Results Comparison", show_header=True, header_style="bold magenta")
        table.add_column("Mode", style="cyan", width=12)
        table.add_column("Word Count", justify="right", style="yellow", width=10)
        table.add_column("Processing Time", justify="right", style="green", width=15)
        table.add_column("Text Preview", style="white", width=60)
        
        # Raw text row
        raw_preview = raw_text[:60] + "..." if len(raw_text) > 60 else raw_text
        table.add_row("RAW", str(len(raw_text.split())), "0ms", raw_preview)
        
        # Enhanced text row
        if enhanced_result.get("success"):
            enhanced_text = enhanced_result["processed_text"]
            enhanced_preview = enhanced_text[:60] + "..." if len(enhanced_text) > 60 else enhanced_text
            processing_time = enhanced_result["metadata"].get("processing_time_ms", 0)
            table.add_row(
                "ENHANCED", 
                str(enhanced_result["word_count"]), 
                f"{processing_time:.1f}ms",
                enhanced_preview
            )
        else:
            table.add_row("ENHANCED", "Error", "N/A", enhanced_result.get("error", "Unknown error")[:60])
        
        # Structured text row
        if structured_result.get("success"):
            structured_text = structured_result["processed_text"]
            structured_preview = structured_text[:60] + "..." if len(structured_text) > 60 else structured_text
            processing_time = structured_result["metadata"].get("processing_time_ms", 0)
            table.add_row(
                "STRUCTURED", 
                str(structured_result["word_count"]), 
                f"{processing_time:.1f}ms",
                structured_preview
            )
        else:
            table.add_row("STRUCTURED", "Error", "N/A", structured_result.get("error", "Unknown error")[:60])
        
        console.print(table)
        console.print()
        
        # Display full text results
        if enhanced_result.get("success"):
            console.print(Panel(enhanced_result["processed_text"], title="Enhanced Text", border_style="blue"))
        if structured_result.get("success"):
            console.print(Panel(structured_result["processed_text"], title="Structured Summary", border_style="green"))
    
    async def cleanup(self):
        """Clean up created test entries"""
        if not self.created_entries:
            return
            
        console.print(f"\n🧹 Cleaning up {len(self.created_entries)} test entries...")
        
        for entry_id in self.created_entries:
            try:
                response = await self.client.delete(f"{BASE_URL}/entries/{entry_id}")
                if response.status_code == 200:
                    console.print(f"   ✅ Deleted entry {entry_id}")
                else:
                    console.print(f"   ⚠️  Failed to delete entry {entry_id}: {response.status_code}")
            except Exception as e:
                console.print(f"   ❌ Error deleting entry {entry_id}: {str(e)}")
    
    async def run_full_test_suite(self):
        """Run the complete test suite"""
        console.print(Panel.fit("🧪 Entry Processing Modes Test Suite", style="bold blue"))
        console.print()
        
        # Test server connection
        console.print("📡 Testing server connection...")
        if not await self.test_server_connection():
            console.print("❌ Cannot proceed without server connection", style="red")
            return False
        console.print()
        
        # Test Ollama connection
        console.print("🤖 Testing Ollama connection...")
        if not await self.test_ollama_connection():
            console.print("❌ Cannot proceed without Ollama connection", style="red")
            return False
        console.print()
        
        # Test processing modes for each test entry
        all_tests_passed = True
        
        for i, test_entry in enumerate(TEST_ENTRIES, 1):
            console.print(f"📝 Test {i}: {test_entry['description']}")
            console.print("-" * 60)
            
            # Create entry
            entry = await self.create_test_entry(test_entry["raw_text"], test_entry["description"])
            if not entry:
                all_tests_passed = False
                continue
            
            entry_id = entry["id"]
            
            # Test enhanced processing
            console.print("🎨 Testing Enhanced Style processing...")
            enhanced_result = await self.test_processing_mode(entry_id, "enhanced", "Enhanced Style")
            
            # Test structured processing
            console.print("📋 Testing Structured Summary processing...")
            structured_result = await self.test_processing_mode(entry_id, "structured", "Structured Summary")
            
            # Display comparison
            console.print("\n📊 Results Comparison:")
            await self.display_comparison(test_entry["raw_text"], enhanced_result, structured_result)
            
            if not enhanced_result.get("success") or not structured_result.get("success"):
                all_tests_passed = False
            
            console.print("=" * 80)
            console.print()
        
        # Summary
        if all_tests_passed:
            console.print(Panel("🎉 All tests passed! Processing modes are working correctly.", style="bold green"))
        else:
            console.print(Panel("⚠️ Some tests failed. Check the output above for details.", style="bold yellow"))
        
        # Cleanup
        await self.cleanup()
        
        return all_tests_passed


async def main():
    """Main test function"""
    console.print("Starting Entry Processing Modes Test...")
    console.print(f"Target server: {BASE_URL}")
    console.print()
    
    async with ProcessingModeTester() as tester:
        success = await tester.run_full_test_suite()
        
    if success:
        console.print("\n✅ Test suite completed successfully!")
        sys.exit(0)
    else:
        console.print("\n❌ Test suite completed with failures!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
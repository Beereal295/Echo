#!/usr/bin/env python3
"""
Test script for Entry Processing API (Task 3.3)
Tests the complete entry processing workflow with queue system
"""

import asyncio
import json
import sys
import time
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
        "raw_text": "So today I had this really important meeting at work and um I was really nervous about it. The presentation went better than expected though. My manager said she was impressed with the research I did. I felt pretty good about that. Oh and I also went for a walk after work which helped me unwind. The weather was nice too.",
        "description": "Work meeting success with evening walk"
    },
    {
        "raw_text": "Feeling kind of down today you know? I've been thinking about my relationship with Sarah and I'm not sure where we stand. We had that argument last week and we haven't really talked about it since. Maybe I should reach out first but I'm worried about making things worse. I just want us to be okay again.",
        "description": "Relationship concerns and anxiety"
    },
    {
        "raw_text": "Had an amazing day hiking with friends! We did the mountain trail that I've been wanting to try for months. The view from the top was incredible. Sarah took some great photos. We stopped for lunch at this cute little cafe on the way back. Felt so refreshed and energized by the end of the day. Need to do this more often.",
        "description": "Hiking adventure with friends"
    }
]


class EntryProcessingTester:
    """Test class for entry processing API"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.created_entries = []
        self.processing_jobs = []
        
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
                data = result.get("data", {})
                connection_info = data.get("connection", {})
                
                console.print("✅ Ollama connection successful", style="green")
                console.print(f"   Connected: {connection_info.get('connected', False)}")
                console.print(f"   Models available: {connection_info.get('model_count', 0)}")
                console.print(f"   Service ready: {data.get('service_ready', False)}")
                
                # Return true if connected and has models
                return connection_info.get('connected', False) and connection_info.get('model_count', 0) > 0
            else:
                console.print(f"❌ Ollama test failed with status {response.status_code}", style="red")
                console.print(f"   Response: {response.text}")
                return False
        except Exception as e:
            console.print(f"❌ Ollama connection failed: {str(e)}", style="red")
            return False
    
    async def test_create_and_process_entry(self, raw_text: str, description: str) -> Dict[str, Any]:
        """Test creating an entry and processing it in multiple modes"""
        try:
            payload = {
                "raw_text": raw_text,
                "modes": ["enhanced", "structured"]
            }
            
            console.print(f"📝 Creating and processing entry: {description}")
            
            response = await self.client.post(f"{BASE_URL}/entries/create-and-process", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                entry_id = result["entry_id"]
                jobs = result["jobs"]
                
                self.created_entries.append(entry_id)
                for job in jobs:
                    self.processing_jobs.append(job["job_id"])
                
                console.print(f"✅ Entry created (ID: {entry_id}) with {len(jobs)} processing jobs")
                
                # Display job information
                for job in jobs:
                    console.print(f"   🔄 {job['mode'].upper()} processing job: {job['job_id']}")
                
                return {
                    "success": True,
                    "entry_id": entry_id,
                    "jobs": jobs,
                    "raw_entry": result["raw_entry"]
                }
            else:
                console.print(f"❌ Failed to create entry: {response.status_code}", style="red")
                console.print(f"   Response: {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            console.print(f"❌ Error creating entry: {str(e)}", style="red")
            return {"success": False, "error": str(e)}
    
    async def wait_for_job_completion(self, job_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Wait for a processing job to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = await self.client.get(f"{BASE_URL}/entries/processing/job/{job_id}")
                
                if response.status_code == 200:
                    job_data = response.json()
                    status = job_data.get("status")
                    
                    if status in ["completed", "failed"]:
                        return job_data
                    
                    # Still processing, wait a bit
                    await asyncio.sleep(1)
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Timeout waiting for job completion"}
    
    async def get_processed_entry(self, entry_id: int) -> Dict[str, Any]:
        """Get the fully processed entry"""
        try:
            response = await self.client.get(f"{BASE_URL}/entries/{entry_id}")
            
            if response.status_code == 200:
                return {"success": True, "entry": response.json()}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_queue_status(self) -> Dict[str, Any]:
        """Test getting processing queue status"""
        try:
            response = await self.client.get(f"{BASE_URL}/entries/processing/queue/status")
            
            if response.status_code == 200:
                status = response.json()
                console.print("📊 Processing Queue Status:")
                console.print(f"   Total jobs: {status.get('total_jobs', 0)}")
                console.print(f"   Queue size: {status.get('queue_size', 0)}")
                console.print(f"   Pending: {status.get('pending', 0)}")
                console.print(f"   Processing: {status.get('processing', 0)}")  
                console.print(f"   Completed: {status.get('completed', 0)}")
                console.print(f"   Failed: {status.get('failed', 0)}")
                console.print(f"   Worker active: {status.get('worker_active', False)}")
                return {"success": True, "status": status}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def display_processing_results(self, entry_id: int, jobs: list):
        """Display the results of processing"""
        
        # Wait for all jobs to complete
        console.print(f"\n⏳ Waiting for processing jobs to complete...")
        
        completed_jobs = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            for job in jobs:
                task = progress.add_task(f"Processing {job['mode']} mode...", total=None)
                
                job_result = await self.wait_for_job_completion(job["job_id"])
                
                if job_result.get("status") == "completed":
                    progress.update(task, description=f"✅ {job['mode']} completed")
                    completed_jobs.append(job_result)
                else:
                    progress.update(task, description=f"❌ {job['mode']} failed")
                    console.print(f"   Error: {job_result.get('error_message', 'Unknown error')}")
        
        # Get the final processed entry
        entry_result = await self.get_processed_entry(entry_id)
        
        if not entry_result["success"]:
            console.print(f"❌ Failed to retrieve processed entry: {entry_result['error']}")
            return
        
        entry = entry_result["entry"]
        
        # Create comparison table
        table = Table(title="Processing Results", show_header=True, header_style="bold magenta")
        table.add_column("Mode", style="cyan", width=12)
        table.add_column("Word Count", justify="right", style="yellow", width=12)  
        table.add_column("Processing Time", justify="right", style="green", width=15)
        table.add_column("Status", style="white", width=12)
        table.add_column("Text Preview", style="white", width=50)
        
        # Raw text row
        raw_text = entry["raw_text"]
        raw_preview = raw_text[:50] + "..." if len(raw_text) > 50 else raw_text
        table.add_row("RAW", str(len(raw_text.split())), "0ms", "✅ Original", raw_preview)
        
        # Enhanced text row
        if entry.get("enhanced_text"):
            enhanced_text = entry["enhanced_text"]
            enhanced_preview = enhanced_text[:50] + "..." if len(enhanced_text) > 50 else enhanced_text
            
            # Find processing metadata for enhanced mode
            processing_time = "N/A"
            if entry.get("processing_metadata"):
                metadata = entry["processing_metadata"]
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        pass
                if isinstance(metadata, dict):
                    processing_time = f"{metadata.get('processing_time_ms', 0):.1f}ms"
            
            table.add_row("ENHANCED", str(len(enhanced_text.split())), processing_time, "✅ Complete", enhanced_preview)
        else:
            table.add_row("ENHANCED", "0", "N/A", "❌ Missing", "Not processed")
        
        # Structured text row  
        if entry.get("structured_summary"):
            structured_text = entry["structured_summary"]
            structured_preview = structured_text[:50] + "..." if len(structured_text) > 50 else structured_text
            table.add_row("STRUCTURED", str(len(structured_text.split())), "N/A", "✅ Complete", structured_preview)
        else:
            table.add_row("STRUCTURED", "0", "N/A", "❌ Missing", "Not processed")
        
        console.print(table)
        console.print()
        
        # Display full text results
        if entry.get("enhanced_text"):
            console.print(Panel(entry["enhanced_text"], title="Enhanced Text", border_style="blue"))
        if entry.get("structured_summary"):
            console.print(Panel(entry["structured_summary"], title="Structured Summary", border_style="green"))
    
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
        console.print(Panel.fit("🧪 Entry Processing API Test Suite (Task 3.3)", style="bold blue"))
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
        
        # Test processing queue status
        console.print("🔍 Testing processing queue status...")
        queue_result = await self.test_queue_status()
        if not queue_result["success"]:
            console.print(f"❌ Queue status check failed: {queue_result['error']}", style="red")
            return False
        console.print()
        
        # Test entry processing for each test case
        all_tests_passed = True
        
        for i, test_entry in enumerate(TEST_ENTRIES, 1):
            console.print(f"📝 Test {i}: {test_entry['description']}")
            console.print("-" * 70)
            
            # Create and process entry
            result = await self.test_create_and_process_entry(
                test_entry["raw_text"], 
                test_entry["description"]
            )
            
            if not result["success"]:
                all_tests_passed = False
                continue
            
            # Wait for processing and display results
            await self.display_processing_results(result["entry_id"], result["jobs"])
            
            console.print("=" * 80)
            console.print()
        
        # Final queue status check
        console.print("📊 Final processing queue status...")
        await self.test_queue_status()
        console.print()
        
        # Summary
        if all_tests_passed:
            console.print(Panel("🎉 All tests passed! Entry Processing API is working correctly.", style="bold green"))
        else:
            console.print(Panel("⚠️ Some tests failed. Check the output above for details.", style="bold yellow"))
        
        # Cleanup
        await self.cleanup()
        
        return all_tests_passed


async def main():
    """Main test function"""
    console.print("Starting Entry Processing API Test...")
    console.print(f"Target server: {BASE_URL}")
    console.print()
    
    async with EntryProcessingTester() as tester:
        success = await tester.run_full_test_suite()
        
    if success:
        console.print("\n✅ Test suite completed successfully!")
        sys.exit(0)
    else:
        console.print("\n❌ Test suite completed with failures!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
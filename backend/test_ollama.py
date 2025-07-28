#!/usr/bin/env python3
"""
Test script for Ollama service integration
Tests connection, model discovery, and text generation
"""

import asyncio
import sys
import httpx
from httpx import ASGITransport

# Add app directory to path for imports
sys.path.append('./app')

from app.main import app


class OllamaTester:
    """Test Ollama service functionality"""
    
    def __init__(self):
        self.client = None
        print("🦙 Echo Ollama Service Tester")
        print("=" * 35)
    
    async def setup(self):
        """Initialize test environment"""
        print("⚙️  Setting up test environment...")
        
        try:
            self.client = httpx.AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            )
            print("[OK] Test environment initialized")
            return True
        except Exception as e:
            print(f"[ERROR] Setup failed: {e}")
            return False
    
    async def test_ollama_endpoints(self):
        """Test all Ollama API endpoints"""
        print("\n🔍 Testing Ollama API Endpoints")
        print("-" * 32)
        
        endpoints = [
            ("GET", "/api/v1/ollama/status", "Service Status"),
            ("GET", "/api/v1/ollama/models", "List Models"),
            ("POST", "/api/v1/ollama/test", "Service Test")
        ]
        
        for method, endpoint, test_name in endpoints:
            try:
                if method == "GET":
                    response = await self.client.get(endpoint)
                else:
                    response = await self.client.post(endpoint)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"[OK] {test_name}")
                    
                    # Show specific info for each endpoint
                    if "status" in endpoint:
                        data = result['data']
                        print(f"     Connected: {'✅' if data.get('connected') else '❌'}")
                        if data.get('connected'):
                            print(f"     URL: {data.get('base_url')}")
                            print(f"     Models: {data.get('model_count', 0)}")
                            print(f"     Default: {data.get('default_model')}")
                        else:
                            print(f"     Error: {data.get('error', 'Unknown')}")
                    
                    elif "models" in endpoint:
                        data = result['data']
                        models = data.get('models', [])
                        print(f"     Found {len(models)} models")
                        for model in models[:3]:  # Show first 3
                            size_info = f"{model['size_gb']:.1f}GB" if model['size_gb'] >= 1 else f"{model['size_mb']:.0f}MB"
                            print(f"     - {model['name']} ({size_info})")
                        if len(models) > 3:
                            print(f"     ... and {len(models) - 3} more")
                    
                    elif "test" in endpoint:
                        data = result['data']
                        print(f"     Service Ready: {'✅' if data.get('service_ready') else '❌'}")
                        
                        connection = data.get('connection', {})
                        print(f"     Connection: {'✅' if connection.get('connected') else '❌'}")
                        
                        gen_test = data.get('generation_test')
                        if gen_test:
                            if gen_test.get('success'):
                                print(f"     Generation Test: ✅ ({gen_test.get('model_used')})")
                            else:
                                print(f"     Generation Test: ❌ ({gen_test.get('error', 'Unknown error')})")
                
                elif response.status_code == 503:
                    print(f"[INFO] {test_name}: Service unavailable (Ollama not running)")
                    if "status" in endpoint:
                        result = response.json()
                        print(f"       {result.get('detail', 'No details')}")
                else:
                    print(f"[ERROR] {test_name}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"[ERROR] {test_name}: {e}")
    
    async def test_text_generation(self):
        """Test text generation if Ollama is available"""
        print("\n📝 Testing Text Generation")
        print("-" * 27)
        
        # First check if Ollama is available
        try:
            status_response = await self.client.get("/api/v1/ollama/status")
            if status_response.status_code != 200:
                print("[INFO] Ollama not available - skipping generation tests")
                return
                
            status_data = status_response.json()['data']
            if not status_data.get('connected'):
                print("[INFO] Ollama not connected - skipping generation tests")
                return
        except Exception as e:
            print(f"[INFO] Cannot check Ollama status: {e}")
            return
        
        # Test simple generation
        generation_tests = [
            {
                "name": "Basic Generation",
                "prompt": "What is the capital of France?",
                "max_tokens": 50
            },
            {
                "name": "System Prompt",
                "prompt": "Hello there!",
                "system": "You are a helpful assistant. Keep responses short.",
                "max_tokens": 30
            }
        ]
        
        for test in generation_tests:
            try:
                print(f"\n{test['name']}:")
                print(f"  Prompt: '{test['prompt']}'")
                
                request_data = {
                    "prompt": test["prompt"],
                    "max_tokens": test.get("max_tokens", 100),
                    "temperature": 0.7
                }
                
                if "system" in test:
                    request_data["system"] = test["system"]
                    print(f"  System: '{test['system']}'")
                
                response = await self.client.post(
                    "/api/v1/ollama/generate",
                    json=request_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    data = result['data']
                    
                    print(f"[OK] Generated response:")
                    print(f"     Model: {data['model']}")
                    print(f"     Response: '{data['response'][:100]}{'...' if len(data['response']) > 100 else ''}'")
                    print(f"     Duration: {data['total_duration_seconds']:.2f}s")
                    print(f"     Tokens/sec: {data['tokens_per_second']:.1f}")
                    
                elif response.status_code == 404:
                    print("[ERROR] Model not found")
                elif response.status_code == 503:
                    print("[INFO] Ollama service unavailable")
                else:
                    print(f"[ERROR] Generation failed: HTTP {response.status_code}")
                    print(f"         {response.text}")
                    
            except Exception as e:
                print(f"[ERROR] {test['name']} failed: {e}")
    
    async def test_chat_completion(self):
        """Test chat completion functionality"""
        print("\n💬 Testing Chat Completion")
        print("-" * 27)
        
        # Check if Ollama is available
        try:
            status_response = await self.client.get("/api/v1/ollama/status")
            if status_response.status_code != 200:
                print("[INFO] Ollama not available - skipping chat tests")
                return
                
            status_data = status_response.json()['data']
            if not status_data.get('connected'):
                print("[INFO] Ollama not connected - skipping chat tests")
                return
        except Exception as e:
            print(f"[INFO] Cannot check Ollama status: {e}")
            return
        
        # Test chat completion
        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant. Be concise."},
                {"role": "user", "content": "Explain what a journal is in one sentence."}
            ]
            
            print("Chat Messages:")
            for msg in messages:
                print(f"  {msg['role']}: {msg['content']}")
            
            request_data = {
                "messages": messages,
                "max_tokens": 50,
                "temperature": 0.7
            }
            
            response = await self.client.post(
                "/api/v1/ollama/chat",
                json=request_data
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result['data']
                
                print(f"[OK] Chat completion:")
                print(f"     Model: {data['model']}")
                print(f"     Response: '{data['message']['content']}'")
                print(f"     Duration: {data['total_duration_seconds']:.2f}s")
                
            elif response.status_code == 404:
                print("[ERROR] Model not found")
            elif response.status_code == 503:
                print("[INFO] Ollama service unavailable")
            else:
                print(f"[ERROR] Chat completion failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"[ERROR] Chat completion test failed: {e}")
    
    async def test_model_management(self):
        """Test model discovery and info"""
        print("\n🤖 Testing Model Management")
        print("-" * 28)
        
        try:
            # Get models
            response = await self.client.get("/api/v1/ollama/models")
            
            if response.status_code == 200:
                result = response.json()
                models = result['data']['models']
                
                if models:
                    print(f"[OK] Found {len(models)} models")
                    
                    # Test getting info for first model
                    first_model = models[0]['name']
                    print(f"\nTesting model info for: {first_model}")
                    
                    info_response = await self.client.get(f"/api/v1/ollama/models/{first_model}")
                    
                    if info_response.status_code == 200:
                        info_result = info_response.json()
                        info_data = info_result['data']
                        
                        print(f"[OK] Model info retrieved:")
                        print(f"     Name: {info_data['name']}")
                        print(f"     Has modelfile: {'✅' if info_data.get('modelfile') else '❌'}")
                        print(f"     Has parameters: {'✅' if info_data.get('parameters') else '❌'}")
                        print(f"     Has template: {'✅' if info_data.get('template') else '❌'}")
                    else:
                        print(f"[ERROR] Model info failed: HTTP {info_response.status_code}")
                else:
                    print("[INFO] No models found")
                    
            elif response.status_code == 503:
                print("[INFO] Ollama service unavailable")
            else:
                print(f"[ERROR] Model listing failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"[ERROR] Model management test failed: {e}")
    
    async def cleanup(self):
        """Clean up resources"""
        if self.client:
            await self.client.aclose()


async def main():
    """Main test runner"""
    tester = OllamaTester()
    
    try:
        if not await tester.setup():
            return 1
        
        # Run all tests
        await tester.test_ollama_endpoints()
        await tester.test_model_management()
        await tester.test_text_generation()
        await tester.test_chat_completion()
        
        print("\n✅ Ollama tests completed!")
        print("\n💡 Ollama service provides:")
        print("   • Local LLM integration via REST API")
        print("   • Model discovery and management")
        print("   • Text generation and chat completion")
        print("   • Graceful fallbacks when unavailable")
        print("   • Configurable connection and timeout")
        print("\n🦙 To use Ollama:")
        print("   1. Install Ollama: https://ollama.ai")
        print("   2. Run: ollama serve")
        print("   3. Pull models: ollama pull llama2")
        print("   4. Test connection with the API")
        
        return 0
        
    except Exception as e:
        print(f"[FATAL ERROR] {e}")
        return 1
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    print("🦙 Echo Ollama Service Integration Test")
    print("Testing local LLM connectivity...")
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"[FATAL] Test runner failed: {e}")
        sys.exit(1)
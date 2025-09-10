#!/usr/bin/env python3
"""
VAPI Integration Test Script

Tests the VAPI webhook integration with the FACT knowledge retrieval system.
Simulates real VAPI calls with proper HMAC signatures and validates responses.
"""

import asyncio
import json
import hmac
import hashlib
import time
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
import sys
from pathlib import Path

# Try to import colorama for colored output, but work without it
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    # Create dummy color classes if colorama not available
    class Fore:
        GREEN = ""
        RED = ""
        YELLOW = ""
        CYAN = ""
        MAGENTA = ""
        RESET = ""
    
    class Style:
        RESET_ALL = ""
    
    HAS_COLOR = False

# Test configuration
TEST_CONFIG = {
    # Use Railway URL for testing deployment, or localhost for local testing
    "base_url": "https://hyper8-fact-production.up.railway.app",  # Change to http://localhost:8000 for local
    "vapi_secret": "test-vapi-secret-key-123",  # Your VAPI secret for HMAC
    "timeout": 30,  # Request timeout in seconds
}

# Test scenarios that simulate real voice agent queries
TEST_SCENARIOS = [
    # Basic licensing questions
    {
        "name": "Basic License Requirements",
        "query": "What are the requirements for a contractor license in Georgia?",
        "expected_keywords": ["Georgia", "requirements", "license", "contractor"],
        "category": "voice_query"
    },
    {
        "name": "Cost Inquiry",
        "query": "How much does a contractor license cost?",
        "expected_keywords": ["cost", "fee", "price", "license"],
        "category": "cost_query"
    },
    {
        "name": "Timeline Question",
        "query": "How long does it take to get licensed?",
        "expected_keywords": ["time", "duration", "process", "days", "weeks"],
        "category": "timeline_query"
    },
    
    # Natural voice variations
    {
        "name": "Colloquial Cost Query",
        "query": "What's the damage for getting licensed?",
        "expected_keywords": ["cost", "investment", "fee"],
        "category": "cost_query"
    },
    {
        "name": "Informal Exam Query",
        "query": "What if I flunk the test?",
        "expected_keywords": ["retake", "fail", "exam", "test"],
        "category": "exam_query"
    },
    {
        "name": "ROI Question",
        "query": "What's the ROI on getting licensed?",
        "expected_keywords": ["return", "investment", "project", "value"],
        "category": "roi_query"
    },
    
    # State-specific queries
    {
        "name": "Nevada Requirements",
        "query": "Nevada contractor license requirements",
        "expected_keywords": ["Nevada", "requirements", "license"],
        "category": "state_specific"
    },
    {
        "name": "California Bonding",
        "query": "California surety bond requirements",
        "expected_keywords": ["California", "surety", "bond"],
        "category": "state_specific"
    },
    
    # Complex multi-part questions
    {
        "name": "Complex Requirements",
        "query": "I'm in Texas and want to know about license requirements and costs",
        "expected_keywords": ["Texas", "requirements", "cost"],
        "category": "complex_query"
    },
    {
        "name": "Comparison Query",
        "query": "Should I DIY the licensing or hire a professional?",
        "expected_keywords": ["DIY", "professional", "service", "help"],
        "category": "comparison_query"
    }
]


def generate_hmac_signature(payload: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature for VAPI webhook authentication."""
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def create_vapi_message(query: str, call_id: Optional[str] = None) -> Dict[str, Any]:
    """Create a VAPI-formatted message payload."""
    if not call_id:
        call_id = f"call_{int(time.time() * 1000)}"
    
    return {
        "message": {
            "type": "function-call",
            "call": {
                "id": call_id,
                "orgId": "org_test_123",
                "createdAt": datetime.utcnow().isoformat() + "Z",
                "phoneNumber": {
                    "number": "+14155551234",
                    "country": "US"
                }
            },
            "functionCall": {
                "name": "searchKnowledge",
                "parameters": {
                    "query": query
                }
            },
            "customer": {
                "number": "+14155555678"
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }


async def test_vapi_endpoint(client: httpx.AsyncClient, query: str, scenario_name: str) -> Dict[str, Any]:
    """Test a single VAPI webhook call."""
    print(f"\n{Fore.CYAN}Testing: {scenario_name}{Style.RESET_ALL}")
    print(f"Query: '{query}'")
    
    # Create VAPI message
    payload = create_vapi_message(query)
    payload_str = json.dumps(payload, separators=(',', ':'))
    
    # Generate HMAC signature
    signature = generate_hmac_signature(payload_str, TEST_CONFIG["vapi_secret"])
    
    # Set headers as VAPI would
    headers = {
        "Content-Type": "application/json",
        "x-vapi-signature": signature,
        "x-vapi-timestamp": str(int(time.time())),
        "User-Agent": "VAPI-Webhook/1.0"
    }
    
    # Send request
    start_time = time.time()
    
    try:
        response = await client.post(
            f"{TEST_CONFIG['base_url']}/vapi/webhook",
            json=payload,
            headers=headers,
            timeout=TEST_CONFIG["timeout"]
        )
        
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Parse response
        result = response.json()
        
        # Analyze response
        success = response.status_code == 200
        has_results = bool(result.get("results", []))
        
        if success and has_results:
            top_result = result["results"][0]
            print(f"{Fore.GREEN}✓ Success{Style.RESET_ALL} - Status: {response.status_code}")
            print(f"  Response Time: {response_time:.0f}ms")
            print(f"  Top Result: {top_result.get('question', 'N/A')[:80]}...")
            print(f"  Score: {top_result.get('metadata', {}).get('score', 0):.2f}")
            print(f"  Confidence: {top_result.get('metadata', {}).get('confidence', 0):.1%}")
        else:
            print(f"{Fore.RED}✗ Failed{Style.RESET_ALL} - Status: {response.status_code}")
            print(f"  Response: {result}")
        
        return {
            "scenario": scenario_name,
            "query": query,
            "success": success,
            "status_code": response.status_code,
            "response_time_ms": response_time,
            "has_results": has_results,
            "result_count": len(result.get("results", [])),
            "top_score": result["results"][0].get("metadata", {}).get("score", 0) if has_results else 0,
            "error": result.get("error")
        }
        
    except httpx.TimeoutException:
        print(f"{Fore.RED}✗ Timeout{Style.RESET_ALL} - Request exceeded {TEST_CONFIG['timeout']}s")
        return {
            "scenario": scenario_name,
            "query": query,
            "success": False,
            "error": "Request timeout"
        }
    except Exception as e:
        print(f"{Fore.RED}✗ Error{Style.RESET_ALL} - {str(e)}")
        return {
            "scenario": scenario_name,
            "query": query,
            "success": False,
            "error": str(e)
        }


async def test_search_function_format():
    """Test the searchKnowledge function call format specifically."""
    print(f"\n{Fore.YELLOW}Testing searchKnowledge Function Format{Style.RESET_ALL}")
    print("=" * 70)
    
    async with httpx.AsyncClient() as client:
        # Test different function call formats
        test_formats = [
            {
                "name": "Standard Format",
                "functionCall": {
                    "name": "searchKnowledge",
                    "parameters": {
                        "query": "Georgia license requirements"
                    }
                }
            },
            {
                "name": "With Category Filter",
                "functionCall": {
                    "name": "searchKnowledge",
                    "parameters": {
                        "query": "license cost",
                        "category": "cost"
                    }
                }
            },
            {
                "name": "With State Filter",
                "functionCall": {
                    "name": "searchKnowledge",
                    "parameters": {
                        "query": "contractor requirements",
                        "state": "CA"
                    }
                }
            },
            {
                "name": "With Limit",
                "functionCall": {
                    "name": "searchKnowledge",
                    "parameters": {
                        "query": "exam preparation",
                        "limit": 3
                    }
                }
            }
        ]
        
        for test_format in test_formats:
            print(f"\n{Fore.CYAN}Testing: {test_format['name']}{Style.RESET_ALL}")
            
            # Create full VAPI message
            payload = {
                "message": {
                    "type": "function-call",
                    "call": {
                        "id": f"call_{int(time.time() * 1000)}",
                        "orgId": "org_test_123"
                    },
                    "functionCall": test_format["functionCall"]
                }
            }
            
            payload_str = json.dumps(payload, separators=(',', ':'))
            signature = generate_hmac_signature(payload_str, TEST_CONFIG["vapi_secret"])
            
            headers = {
                "Content-Type": "application/json",
                "x-vapi-signature": signature
            }
            
            try:
                response = await client.post(
                    f"{TEST_CONFIG['base_url']}/vapi/webhook",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"{Fore.GREEN}✓ Format accepted{Style.RESET_ALL}")
                    result = response.json()
                    print(f"  Results: {len(result.get('results', []))} items")
                else:
                    print(f"{Fore.RED}✗ Format rejected{Style.RESET_ALL}")
                    print(f"  Status: {response.status_code}")
                    print(f"  Error: {response.text[:200]}")
                    
            except Exception as e:
                print(f"{Fore.RED}✗ Request failed: {e}{Style.RESET_ALL}")


async def test_authentication():
    """Test VAPI webhook authentication (HMAC signature validation)."""
    print(f"\n{Fore.YELLOW}Testing VAPI Authentication{Style.RESET_ALL}")
    print("=" * 70)
    
    async with httpx.AsyncClient() as client:
        payload = create_vapi_message("test query")
        payload_str = json.dumps(payload, separators=(',', ':'))
        
        # Test with correct signature
        print(f"\n{Fore.CYAN}Test 1: Valid HMAC Signature{Style.RESET_ALL}")
        correct_signature = generate_hmac_signature(payload_str, TEST_CONFIG["vapi_secret"])
        
        response = await client.post(
            f"{TEST_CONFIG['base_url']}/vapi/webhook",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "x-vapi-signature": correct_signature
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"{Fore.GREEN}✓ Authentication successful{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠ Unexpected status: {response.status_code}{Style.RESET_ALL}")
            print(f"  Note: Server might not have authentication enabled")
        
        # Test with incorrect signature
        print(f"\n{Fore.CYAN}Test 2: Invalid HMAC Signature{Style.RESET_ALL}")
        wrong_signature = "invalid_signature_12345"
        
        response = await client.post(
            f"{TEST_CONFIG['base_url']}/vapi/webhook",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "x-vapi-signature": wrong_signature
            },
            timeout=10
        )
        
        if response.status_code == 401:
            print(f"{Fore.GREEN}✓ Invalid signature rejected correctly{Style.RESET_ALL}")
        elif response.status_code == 200:
            print(f"{Fore.YELLOW}⚠ Server accepted invalid signature{Style.RESET_ALL}")
            print(f"  Warning: Authentication might not be enabled")
        else:
            print(f"{Fore.RED}✗ Unexpected status: {response.status_code}{Style.RESET_ALL}")
        
        # Test without signature
        print(f"\n{Fore.CYAN}Test 3: Missing HMAC Signature{Style.RESET_ALL}")
        
        response = await client.post(
            f"{TEST_CONFIG['base_url']}/vapi/webhook",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 401:
            print(f"{Fore.GREEN}✓ Missing signature rejected correctly{Style.RESET_ALL}")
        elif response.status_code == 200:
            print(f"{Fore.YELLOW}⚠ Server accepted request without signature{Style.RESET_ALL}")
            print(f"  Warning: Authentication might not be enabled")
        else:
            print(f"{Fore.RED}✗ Unexpected status: {response.status_code}{Style.RESET_ALL}")


async def test_performance():
    """Test response time for voice interaction requirements."""
    print(f"\n{Fore.YELLOW}Testing Performance for Voice Interactions{Style.RESET_ALL}")
    print("=" * 70)
    
    async with httpx.AsyncClient() as client:
        response_times = []
        
        # Run multiple queries to test performance
        test_queries = [
            "Georgia contractor license",
            "How much does it cost?",
            "What are the requirements?",
            "Nevada licensing",
            "ROI on getting licensed"
        ]
        
        for query in test_queries:
            payload = create_vapi_message(query)
            payload_str = json.dumps(payload, separators=(',', ':'))
            signature = generate_hmac_signature(payload_str, TEST_CONFIG["vapi_secret"])
            
            headers = {
                "Content-Type": "application/json",
                "x-vapi-signature": signature
            }
            
            start_time = time.time()
            
            try:
                response = await client.post(
                    f"{TEST_CONFIG['base_url']}/vapi/webhook",
                    json=payload,
                    headers=headers,
                    timeout=5  # Strict timeout for voice
                )
                
                response_time = (time.time() - start_time) * 1000
                response_times.append(response_time)
                
                if response_time < 100:
                    status = f"{Fore.GREEN}✓ Excellent{Style.RESET_ALL}"
                elif response_time < 300:
                    status = f"{Fore.YELLOW}⚠ Good{Style.RESET_ALL}"
                else:
                    status = f"{Fore.RED}✗ Slow{Style.RESET_ALL}"
                
                print(f"Query: '{query[:30]}...' - {response_time:.0f}ms {status}")
                
            except httpx.TimeoutException:
                print(f"Query: '{query[:30]}...' - {Fore.RED}TIMEOUT (>5s){Style.RESET_ALL}")
            except Exception as e:
                print(f"Query: '{query[:30]}...' - {Fore.RED}ERROR: {e}{Style.RESET_ALL}")
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            print(f"\n{Fore.CYAN}Performance Summary:{Style.RESET_ALL}")
            print(f"  Average: {avg_time:.0f}ms")
            print(f"  Minimum: {min_time:.0f}ms")
            print(f"  Maximum: {max_time:.0f}ms")
            
            if avg_time < 100:
                print(f"  {Fore.GREEN}✓ Excellent for voice interactions{Style.RESET_ALL}")
            elif avg_time < 300:
                print(f"  {Fore.YELLOW}⚠ Acceptable for voice interactions{Style.RESET_ALL}")
            else:
                print(f"  {Fore.RED}✗ Too slow for smooth voice interactions{Style.RESET_ALL}")


async def main():
    """Run all VAPI integration tests."""
    print(f"{Fore.MAGENTA}{'=' * 70}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}VAPI Integration Test Suite{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'=' * 70}{Style.RESET_ALL}")
    print(f"Testing URL: {TEST_CONFIG['base_url']}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if server is reachable
    print(f"\n{Fore.YELLOW}Checking Server Health...{Style.RESET_ALL}")
    async with httpx.AsyncClient() as client:
        try:
            health_response = await client.get(
                f"{TEST_CONFIG['base_url']}/health",
                timeout=5
            )
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"{Fore.GREEN}✓ Server is healthy{Style.RESET_ALL}")
                print(f"  Status: {health_data.get('status')}")
                print(f"  Enhanced Retriever: {health_data.get('metrics', {}).get('enhanced_retriever', False)}")
                print(f"  Entries: {health_data.get('metrics', {}).get('enhanced_retriever_entries', 0)}")
            else:
                print(f"{Fore.RED}✗ Server returned status {health_response.status_code}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}✗ Cannot reach server: {e}{Style.RESET_ALL}")
            print("Please check the URL or start the server locally")
            return
    
    # Run authentication tests
    await test_authentication()
    
    # Test function call formats
    await test_search_function_format()
    
    # Test performance
    await test_performance()
    
    # Run main test scenarios
    print(f"\n{Fore.YELLOW}Running Query Test Scenarios{Style.RESET_ALL}")
    print("=" * 70)
    
    results = []
    async with httpx.AsyncClient() as client:
        for scenario in TEST_SCENARIOS:
            result = await test_vapi_endpoint(
                client,
                scenario["query"],
                scenario["name"]
            )
            results.append(result)
            await asyncio.sleep(0.5)  # Small delay between tests
    
    # Summary
    print(f"\n{Fore.MAGENTA}{'=' * 70}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}Test Summary{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'=' * 70}{Style.RESET_ALL}")
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    failed_tests = total_tests - successful_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"{Fore.GREEN}Successful: {successful_tests}{Style.RESET_ALL}")
    print(f"{Fore.RED}Failed: {failed_tests}{Style.RESET_ALL}")
    
    if successful_tests == total_tests:
        print(f"\n{Fore.GREEN}🎉 All tests passed! VAPI integration is working correctly.{Style.RESET_ALL}")
    elif successful_tests > total_tests * 0.8:
        print(f"\n{Fore.YELLOW}⚠ Most tests passed ({successful_tests}/{total_tests}). Some issues to address.{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}❌ Many tests failed ({failed_tests}/{total_tests}). VAPI integration needs attention.{Style.RESET_ALL}")
    
    # Show failed tests
    if failed_tests > 0:
        print(f"\n{Fore.RED}Failed Tests:{Style.RESET_ALL}")
        for result in results:
            if not result["success"]:
                print(f"  - {result['scenario']}: {result.get('error', 'No results')}")
    
    # Response time analysis
    valid_times = [r["response_time_ms"] for r in results if r.get("response_time_ms")]
    if valid_times:
        avg_response = sum(valid_times) / len(valid_times)
        print(f"\n{Fore.CYAN}Average Response Time: {avg_response:.0f}ms{Style.RESET_ALL}")
        
        if avg_response < 100:
            print(f"  {Fore.GREEN}✓ Excellent for real-time voice{Style.RESET_ALL}")
        elif avg_response < 300:
            print(f"  {Fore.YELLOW}⚠ Acceptable for voice{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}✗ May cause delays in voice conversations{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}Next Steps:{Style.RESET_ALL}")
    print("1. Configure VAPI with your webhook URL: " + TEST_CONFIG['base_url'] + "/vapi/webhook")
    print("2. Set your VAPI secret key for HMAC authentication")
    print("3. Use the 'searchKnowledge' function in your VAPI assistant")
    print("4. Monitor the training API to improve accuracy over time")


if __name__ == "__main__":
    # Check if we should use local or Railway
    if len(sys.argv) > 1 and sys.argv[1] == "local":
        TEST_CONFIG["base_url"] = "http://localhost:8000"
        print("Testing against LOCAL server")
    else:
        print("Testing against RAILWAY deployment")
    
    asyncio.run(main())
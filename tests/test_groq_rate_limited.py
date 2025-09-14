#!/usr/bin/env python3
"""
Rate-limited comprehensive test of FACT system with Groq API
Respects the 30 requests per minute limit (2 seconds between requests)
"""

import asyncio
import json
import time
from typing import Dict, List, Any
import requests
from datetime import datetime

# Test configuration
API_URL = "https://hyper8-fact-fact-system.up.railway.app"
TEST_TIMEOUT = 30
RATE_LIMIT_DELAY = 2.1  # 2.1 seconds between requests to stay under 30/minute

# Test queries covering different aspects
TEST_QUERIES = [
    # Basic Information
    "What is the NASCLA certification?",
    "What states accept NASCLA certification?",
    "How much does a Florida contractor license cost?",
    
    # Complex Queries
    "Compare the contractor licensing requirements between Florida and California",
    "What are the steps to get a general contractor license in Texas?",
    "Explain the difference between a state license and a local license",
    
    # Specific Details
    "What is the minimum net worth requirement for a Florida contractor?",
    "How long is a contractor license valid in Georgia?",
    "What types of work require a specialty contractor license?",
    
    # Process Questions
    "How do I transfer my contractor license to another state?",
    "What happens if my contractor license expires?",
    "Can I work in multiple states with one license?"
]

def make_api_request(query: str, timeout: int = TEST_TIMEOUT) -> Dict[str, Any]:
    """Make a request to the FACT API"""
    try:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "query": query,
            "context": {
                "source": "groq_rate_limited_test",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        response = requests.post(
            f"{API_URL}/query",
            json=payload,
            headers=headers,
            timeout=timeout
        )
        
        return {
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text,
            "response_time": response.elapsed.total_seconds() * 1000
        }
        
    except requests.exceptions.Timeout:
        return {
            "status_code": 408,
            "response": "Request timed out",
            "response_time": timeout * 1000
        }
    except Exception as e:
        return {
            "status_code": 500,
            "response": str(e),
            "response_time": 0
        }

def analyze_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze the quality of a response"""
    analysis = {
        "success": response["status_code"] == 200,
        "has_content": False,
        "response_length": 0,
        "response_time_ms": response["response_time"],
        "performance": "slow" if response["response_time"] > 5000 else "fast" if response["response_time"] < 1000 else "normal"
    }
    
    if analysis["success"] and isinstance(response["response"], dict):
        answer = response["response"].get("answer", "")
        analysis["has_content"] = len(answer) > 50
        analysis["response_length"] = len(answer)
    
    return analysis

def print_test_header():
    """Print test header"""
    print("\n" + "="*70)
    print("🧪 RATE-LIMITED GROQ API INTEGRATION TEST")
    print("="*70)
    print(f"API URL: {API_URL}")
    print(f"Model: openai/gpt-oss-120b (via Groq)")
    print(f"Rate Limit: 30 requests/minute ({RATE_LIMIT_DELAY}s delay)")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Queries: {len(TEST_QUERIES)}")
    print(f"Estimated Duration: {len(TEST_QUERIES) * RATE_LIMIT_DELAY:.0f} seconds")
    print("="*70 + "\n")

def print_query_result(idx: int, query: str, result: Dict[str, Any], analysis: Dict[str, Any]):
    """Print individual query result"""
    status_icon = "✅" if analysis["success"] else "❌"
    perf_icon = "🚀" if analysis["performance"] == "fast" else "⚡" if analysis["performance"] == "normal" else "🐌"
    
    print(f"\n{idx}. {query[:60]}...")
    print(f"   {status_icon} Status: {result['status_code']} | {perf_icon} Time: {analysis['response_time_ms']:.0f}ms")
    
    if analysis["success"]:
        print(f"   📝 Response length: {analysis['response_length']} chars")
        if isinstance(result["response"], dict):
            answer = result["response"].get("answer", "")
            if answer:
                preview = answer[:150].replace("\n", " ")
                print(f"   Preview: {preview}...")
            else:
                print(f"   ⚠️  Empty response received")

def run_rate_limited_test():
    """Run comprehensive test suite with rate limiting"""
    print_test_header()
    
    results = []
    successful = 0
    failed = 0
    total_response_time = 0
    
    print("🔄 Starting rate-limited test queries...\n")
    print(f"⏰ Each request will wait {RATE_LIMIT_DELAY}s to respect rate limits\n")
    
    start_time = time.time()
    
    for idx, query in enumerate(TEST_QUERIES, 1):
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Testing query {idx}/{len(TEST_QUERIES)}...")
        print(f"   Query: {query[:80]}...")
        
        result = make_api_request(query)
        analysis = analyze_response(result)
        
        results.append({
            "query": query,
            "result": result,
            "analysis": analysis
        })
        
        if analysis["success"]:
            successful += 1
            if analysis["has_content"]:
                print(f"   ✅ Success with content ({analysis['response_length']} chars)")
            else:
                print(f"   ⚠️  Success but empty response")
        else:
            failed += 1
            print(f"   ❌ Failed: {result['status_code']} - {result['response'][:100]}")
        
        total_response_time += analysis["response_time_ms"]
        
        # Rate limiting delay (except for last query)
        if idx < len(TEST_QUERIES):
            print(f"   ⏳ Waiting {RATE_LIMIT_DELAY}s for rate limit...")
            time.sleep(RATE_LIMIT_DELAY)
    
    elapsed_time = time.time() - start_time
    
    # Print detailed results
    print("\n" + "="*70)
    print("📊 DETAILED RESULTS")
    print("="*70)
    
    for idx, item in enumerate(results, 1):
        print_query_result(idx, item["query"], item["result"], item["analysis"])
    
    # Print summary
    print("\n" + "="*70)
    print("📈 TEST SUMMARY")
    print("="*70)
    
    success_rate = (successful / len(TEST_QUERIES)) * 100
    avg_response_time = total_response_time / len(TEST_QUERIES)
    
    print(f"✅ Successful: {successful}/{len(TEST_QUERIES)} ({success_rate:.1f}%)")
    print(f"❌ Failed: {failed}/{len(TEST_QUERIES)}")
    print(f"⏱️  Average Response Time: {avg_response_time:.0f}ms")
    print(f"⏱️  Total Test Duration: {elapsed_time:.1f} seconds")
    
    # Content analysis
    with_content = sum(1 for r in results if r["analysis"]["has_content"])
    without_content = successful - with_content
    
    print(f"\n📝 Content Analysis:")
    print(f"   ✅ With content: {with_content}")
    print(f"   ⚠️  Empty responses: {without_content}")
    print(f"   ❌ Failed requests: {failed}")
    
    # Performance breakdown
    fast = sum(1 for r in results if r["analysis"]["performance"] == "fast")
    normal = sum(1 for r in results if r["analysis"]["performance"] == "normal")
    slow = sum(1 for r in results if r["analysis"]["performance"] == "slow")
    
    print(f"\n📊 Performance Distribution:")
    print(f"   🚀 Fast (<1s): {fast}")
    print(f"   ⚡ Normal (1-5s): {normal}")
    print(f"   🐌 Slow (>5s): {slow}")
    
    # Final verdict
    print("\n" + "="*70)
    if success_rate >= 90 and avg_response_time < 2000:
        print("🎉 EXCELLENT: System performing optimally with Groq!")
    elif success_rate >= 70:
        print("✅ GOOD: System working well with Groq")
    elif success_rate >= 50:
        print("⚠️  FAIR: System partially working, needs attention")
    else:
        print("❌ POOR: System having issues, investigation needed")
    print("="*70)
    
    # Rate limit compliance
    print(f"\n📊 Rate Limit Compliance:")
    actual_rate = len(TEST_QUERIES) / (elapsed_time / 60)
    print(f"   Target: ≤30 requests/minute")
    print(f"   Actual: {actual_rate:.1f} requests/minute")
    if actual_rate <= 30:
        print(f"   ✅ Rate limit respected")
    else:
        print(f"   ⚠️  Rate limit exceeded")
    
    return {
        "success_rate": success_rate,
        "avg_response_time": avg_response_time,
        "successful": successful,
        "failed": failed,
        "with_content": with_content
    }

if __name__ == "__main__":
    try:
        # Check API health first
        print("🔍 Checking API health...")
        health_response = requests.get(f"{API_URL}/health", timeout=10)
        if health_response.status_code == 200:
            print("✅ API is healthy")
        else:
            print(f"⚠️  API health check returned: {health_response.status_code}")
        
        # Check system status
        print("\n🔍 Checking system initialization...")
        test_response = requests.post(
            f"{API_URL}/query",
            json={"query": "test"},
            timeout=10
        )
        if test_response.status_code == 200:
            print("✅ System is initialized and ready")
        else:
            response_text = test_response.text
            print(f"⚠️  System status: {response_text[:200]}")
        
        # Run the comprehensive test
        test_results = run_rate_limited_test()
        
        # Exit with appropriate code
        if test_results["success_rate"] >= 70:
            exit(0)
        else:
            exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
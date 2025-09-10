#!/usr/bin/env python3
"""
Comprehensive Railway API Testing Suite
Tests all endpoints and functionality of the deployed FACT system.
"""

import asyncio
import aiohttp
import json
import time
import hashlib
import hmac
from datetime import datetime
from typing import Dict, List, Any

# Railway API URL
RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

# Test configuration
VAPI_SECRET = "test_secret_key"  # Replace with actual secret for production tests

class RailwayAPITester:
    """Comprehensive API testing for Railway deployment."""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "url": RAILWAY_URL,
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0
            }
        }
    
    def add_test_result(self, name: str, passed: bool, details: str = "", data: Any = None):
        """Add a test result to the summary."""
        self.results["tests"].append({
            "name": name,
            "passed": passed,
            "details": details,
            "data": data
        })
        self.results["summary"]["total"] += 1
        if passed:
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    async def test_health_endpoint(self, session: aiohttp.ClientSession):
        """Test the health check endpoint."""
        print("\n1️⃣ Testing Health Endpoint...")
        try:
            async with session.get(f"{RAILWAY_URL}/health") as r:
                if r.status == 200:
                    data = await r.json()
                    self.add_test_result(
                        "Health Check",
                        data["status"] == "healthy",
                        f"Status: {data['status']}, Initialized: {data['initialized']}",
                        data
                    )
                    
                    # Check enhanced retriever
                    if "metrics" in data:
                        entries = data["metrics"].get("enhanced_retriever_entries", 0)
                        self.add_test_result(
                            "Enhanced Retriever",
                            entries > 0,
                            f"Entries loaded: {entries}",
                            {"entries": entries}
                        )
                    
                    print(f"   ✅ Health: {data['status']}")
                    print(f"   ✅ Enhanced Retriever: {data['metrics'].get('enhanced_retriever_entries', 0)} entries")
                else:
                    self.add_test_result("Health Check", False, f"HTTP {r.status}")
                    print(f"   ❌ Health check failed: HTTP {r.status}")
        except Exception as e:
            self.add_test_result("Health Check", False, str(e))
            print(f"   ❌ Health check error: {e}")
    
    async def test_metrics_endpoint(self, session: aiohttp.ClientSession):
        """Test the metrics endpoint."""
        print("\n2️⃣ Testing Metrics Endpoint...")
        try:
            async with session.get(f"{RAILWAY_URL}/metrics") as r:
                if r.status == 200:
                    data = await r.json()
                    self.add_test_result(
                        "Metrics Endpoint",
                        True,
                        "Metrics retrieved successfully",
                        data
                    )
                    print(f"   ✅ Metrics retrieved")
                    print(f"      • Total queries: {data.get('total_queries', 0)}")
                    print(f"      • Cache hit rate: {data.get('cache_hit_rate', 0)}")
                else:
                    self.add_test_result("Metrics Endpoint", False, f"HTTP {r.status}")
                    print(f"   ❌ Metrics failed: HTTP {r.status}")
        except Exception as e:
            self.add_test_result("Metrics Endpoint", False, str(e))
            print(f"   ❌ Metrics error: {e}")
    
    async def test_knowledge_search(self, session: aiohttp.ClientSession):
        """Test knowledge base search functionality."""
        print("\n3️⃣ Testing Knowledge Search...")
        
        test_queries = [
            {
                "query": "Georgia contractor license requirements",
                "expected_state": "GA",
                "expected_category": "state_licensing_requirements"
            },
            {
                "query": "California contractor license",
                "expected_state": "CA",
                "expected_category": "state_licensing_requirements"
            },
            {
                "query": "What is a mechanics lien",
                "expected_category": "insurance_bonding"
            },
            {
                "query": "exam preparation tips",
                "expected_category": "exam_preparation_testing"
            },
            {
                "query": "contractor bond requirements",
                "expected_category": "insurance_bonding"
            }
        ]
        
        for test in test_queries:
            try:
                async with session.post(
                    f"{RAILWAY_URL}/knowledge/search",
                    json={"query": test["query"], "limit": 3}
                ) as r:
                    if r.status == 200:
                        data = await r.json()
                        results = data.get("results", [])
                        
                        if results:
                            top_result = results[0]
                            
                            # Check state match if expected
                            state_match = True
                            if "expected_state" in test:
                                state_match = top_result.get("state") == test["expected_state"]
                            
                            # Check category match if expected
                            category_match = True
                            if "expected_category" in test:
                                category_match = test["expected_category"] in top_result.get("category", "")
                            
                            passed = len(results) > 0 and (state_match or category_match)
                            
                            self.add_test_result(
                                f"Search: {test['query'][:30]}",
                                passed,
                                f"Found {len(results)} results",
                                {"query": test["query"], "results": len(results), "top_match": top_result.get("question")}
                            )
                            
                            status = "✅" if passed else "⚠️"
                            print(f"   {status} '{test['query'][:40]}...'")
                            print(f"      → Found: {top_result['question'][:50]}...")
                            if not state_match and "expected_state" in test:
                                print(f"      ⚠️ State mismatch: expected {test['expected_state']}, got {top_result.get('state')}")
                        else:
                            self.add_test_result(
                                f"Search: {test['query'][:30]}",
                                False,
                                "No results found"
                            )
                            print(f"   ❌ '{test['query'][:40]}...' - No results")
                    else:
                        self.add_test_result(
                            f"Search: {test['query'][:30]}",
                            False,
                            f"HTTP {r.status}"
                        )
            except Exception as e:
                self.add_test_result(
                    f"Search: {test['query'][:30]}",
                    False,
                    str(e)
                )
                print(f"   ❌ Search error: {e}")
    
    async def test_knowledge_stats(self, session: aiohttp.ClientSession):
        """Test knowledge base statistics endpoint."""
        print("\n4️⃣ Testing Knowledge Stats...")
        try:
            async with session.get(f"{RAILWAY_URL}/knowledge/stats") as r:
                if r.status == 200:
                    data = await r.json()
                    total = data.get("total_entries", 0)
                    self.add_test_result(
                        "Knowledge Stats",
                        total > 0,
                        f"Total entries: {total}",
                        data
                    )
                    print(f"   ✅ Total entries: {total}")
                    print(f"   ✅ Categories: {data.get('total_categories', 0)}")
                    print(f"   ✅ States: {data.get('total_states', 0)}")
                else:
                    self.add_test_result("Knowledge Stats", False, f"HTTP {r.status}")
        except Exception as e:
            self.add_test_result("Knowledge Stats", False, str(e))
            print(f"   ❌ Stats error: {e}")
    
    async def test_vapi_webhook(self, session: aiohttp.ClientSession):
        """Test VAPI webhook endpoint."""
        print("\n5️⃣ Testing VAPI Webhook...")
        
        # Prepare test payload
        payload = {
            "message": {
                "role": "user",
                "content": "What are the contractor license requirements for Georgia?"
            },
            "call": {
                "id": "test_call_123",
                "type": "inbound",
                "phoneNumber": "+1234567890"
            }
        }
        
        # Generate signature for authentication
        payload_str = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            VAPI_SECRET.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "Content-Type": "application/json",
            "x-vapi-signature": signature
        }
        
        try:
            async with session.post(
                f"{RAILWAY_URL}/vapi/webhook",
                json=payload,
                headers=headers
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    has_response = bool(data.get("results"))
                    self.add_test_result(
                        "VAPI Webhook",
                        has_response,
                        "Webhook processed successfully" if has_response else "No response generated",
                        data
                    )
                    
                    if has_response:
                        print(f"   ✅ VAPI webhook working")
                        result = data["results"][0] if data.get("results") else {}
                        if result.get("content"):
                            print(f"      → Response: {result['content'][:100]}...")
                    else:
                        print(f"   ⚠️ VAPI webhook returned no results")
                else:
                    text = await r.text()
                    self.add_test_result("VAPI Webhook", False, f"HTTP {r.status}: {text}")
                    print(f"   ❌ VAPI webhook failed: HTTP {r.status}")
        except Exception as e:
            self.add_test_result("VAPI Webhook", False, str(e))
            print(f"   ❌ VAPI webhook error: {e}")
    
    async def test_performance(self, session: aiohttp.ClientSession):
        """Test API performance and response times."""
        print("\n6️⃣ Testing Performance...")
        
        # Test single request latency
        start = time.time()
        async with session.post(
            f"{RAILWAY_URL}/knowledge/search",
            json={"query": "contractor license", "limit": 5}
        ) as r:
            await r.json()
        single_latency = (time.time() - start) * 1000
        
        print(f"   • Single request: {single_latency:.1f}ms")
        
        # Test concurrent requests
        queries = [
            {"query": f"contractor license {state}", "limit": 3}
            for state in ["Georgia", "California", "Florida", "Texas", "New York"]
        ]
        
        start = time.time()
        tasks = [
            session.post(f"{RAILWAY_URL}/knowledge/search", json=q)
            for q in queries
        ]
        responses = await asyncio.gather(*tasks)
        concurrent_time = time.time() - start
        
        for r in responses:
            await r.json()
            r.close()
        
        avg_concurrent = (concurrent_time * 1000) / len(queries)
        
        print(f"   • {len(queries)} concurrent requests: {concurrent_time:.2f}s")
        print(f"   • Average per request: {avg_concurrent:.1f}ms")
        
        self.add_test_result(
            "Performance",
            single_latency < 500 and avg_concurrent < 200,
            f"Single: {single_latency:.1f}ms, Concurrent avg: {avg_concurrent:.1f}ms",
            {
                "single_latency_ms": single_latency,
                "concurrent_requests": len(queries),
                "total_time_s": concurrent_time,
                "avg_latency_ms": avg_concurrent
            }
        )
        
        status = "✅" if single_latency < 500 else "⚠️"
        print(f"   {status} Performance acceptable")
    
    async def test_error_handling(self, session: aiohttp.ClientSession):
        """Test error handling and edge cases."""
        print("\n7️⃣ Testing Error Handling...")
        
        # Test invalid endpoint
        try:
            async with session.get(f"{RAILWAY_URL}/invalid-endpoint") as r:
                self.add_test_result(
                    "404 Handling",
                    r.status == 404,
                    f"HTTP {r.status}"
                )
                status = "✅" if r.status == 404 else "❌"
                print(f"   {status} Invalid endpoint returns 404")
        except:
            self.add_test_result("404 Handling", False, "Exception raised")
        
        # Test invalid search query
        try:
            async with session.post(
                f"{RAILWAY_URL}/knowledge/search",
                json={"query": "", "limit": -1}
            ) as r:
                handled = r.status in [200, 400, 422]
                self.add_test_result(
                    "Invalid Query Handling",
                    handled,
                    f"HTTP {r.status}"
                )
                status = "✅" if handled else "❌"
                print(f"   {status} Invalid query handled gracefully")
        except:
            self.add_test_result("Invalid Query Handling", False, "Exception raised")
        
        # Test large limit
        try:
            async with session.post(
                f"{RAILWAY_URL}/knowledge/search",
                json={"query": "test", "limit": 10000}
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    results = len(data.get("results", []))
                    self.add_test_result(
                        "Large Limit Handling",
                        results <= 1000,
                        f"Returned {results} results"
                    )
                    print(f"   ✅ Large limit capped at {results} results")
        except:
            self.add_test_result("Large Limit Handling", False, "Exception raised")
    
    async def run_all_tests(self):
        """Run all API tests."""
        print("🧪 Railway API Comprehensive Testing")
        print("=" * 70)
        print(f"URL: {RAILWAY_URL}")
        print(f"Time: {datetime.now().isoformat()}")
        
        async with aiohttp.ClientSession() as session:
            await self.test_health_endpoint(session)
            await self.test_metrics_endpoint(session)
            await self.test_knowledge_search(session)
            await self.test_knowledge_stats(session)
            await self.test_vapi_webhook(session)
            await self.test_performance(session)
            await self.test_error_handling(session)
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 Test Summary:")
        print(f"   Total Tests: {self.results['summary']['total']}")
        print(f"   ✅ Passed: {self.results['summary']['passed']}")
        print(f"   ❌ Failed: {self.results['summary']['failed']}")
        
        success_rate = (self.results['summary']['passed'] / self.results['summary']['total']) * 100
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Save detailed results
        with open("railway_api_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Detailed results saved to railway_api_test_results.json")
        
        return success_rate >= 70  # Consider test successful if 70%+ pass

async def main():
    """Main test runner."""
    tester = RailwayAPITester()
    success = await tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
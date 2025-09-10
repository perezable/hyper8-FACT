#!/usr/bin/env python3
"""
Test Railway deployment endpoints to verify what's available.
"""

import httpx
import asyncio
import json
from datetime import datetime

RAILWAY_URL = "https://hyper8-fact-production.up.railway.app"

async def test_endpoints():
    """Test various endpoints to see what's working."""
    
    endpoints = [
        {"method": "GET", "path": "/", "description": "Root"},
        {"method": "GET", "path": "/health", "description": "Health check"},
        {"method": "GET", "path": "/knowledge/stats", "description": "Knowledge stats"},
        {"method": "POST", "path": "/knowledge/search", "description": "Knowledge search", 
         "json": {"query": "Georgia license", "limit": 5}},
        {"method": "POST", "path": "/vapi/webhook", "description": "VAPI webhook",
         "json": {"message": {"type": "function-call", "functionCall": {"name": "searchKnowledge", "parameters": {"query": "test"}}}}},
    ]
    
    print(f"Testing Railway deployment: {RAILWAY_URL}")
    print("=" * 70)
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        for endpoint in endpoints:
            print(f"\n{endpoint['description']} ({endpoint['method']} {endpoint['path']})")
            print("-" * 40)
            
            try:
                if endpoint["method"] == "GET":
                    response = await client.get(f"{RAILWAY_URL}{endpoint['path']}")
                else:  # POST
                    response = await client.post(
                        f"{RAILWAY_URL}{endpoint['path']}", 
                        json=endpoint.get("json", {})
                    )
                
                print(f"Status: {response.status_code}")
                
                # Try to parse JSON response
                try:
                    data = response.json()
                    print(f"Response: {json.dumps(data, indent=2)[:500]}")
                except:
                    print(f"Response (text): {response.text[:500]}")
                    
            except httpx.TimeoutException:
                print("TIMEOUT - Request took too long")
            except Exception as e:
                print(f"ERROR: {e}")
    
    # Now test knowledge search specifically
    print("\n" + "=" * 70)
    print("Testing Knowledge Search Endpoint")
    print("=" * 70)
    
    test_queries = [
        "Georgia contractor license requirements",
        "How much does a license cost?",
        "What's the ROI on getting licensed?"
    ]
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            
            try:
                response = await client.post(
                    f"{RAILWAY_URL}/knowledge/search",
                    json={"query": query, "limit": 3}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✓ Success - Found {len(data.get('results', []))} results")
                    if data.get('results'):
                        result = data['results'][0]
                        print(f"  Top result: {result.get('question', 'N/A')[:80]}...")
                        if 'metadata' in result:
                            meta = result['metadata']
                            print(f"  Score: {meta.get('score', 0):.2f}, Confidence: {meta.get('confidence', 0):.1%}")
                else:
                    print(f"✗ Failed - Status {response.status_code}")
                    
            except Exception as e:
                print(f"✗ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_endpoints())
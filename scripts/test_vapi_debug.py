#!/usr/bin/env python3
"""
Test VAPI webhook debug endpoint.
"""

import httpx
import asyncio
import json

BASE_URL = "https://hyper8-fact-fact-system.up.railway.app"

async def test_debug():
    """Test with various queries."""
    
    queries = [
        ("Georgia", None),
        ("contractor license", None),
        ("Georgia contractor", None),
        ("requirements", "GA"),
        ("license requirements", "GA"),
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for query, state in queries:
            print(f"\n{'='*60}")
            print(f"Query: '{query}' | State: {state}")
            print('-'*60)
            
            # Test knowledge API first
            params = {"query": query, "limit": 1}
            if state:
                params["state"] = state
                
            response = await client.post(
                f"{BASE_URL}/knowledge/search",
                json=params
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["results"]:
                    result = data["results"][0]
                    print(f"✅ Knowledge API found: {result['question'][:50]}...")
                    print(f"   State: {result.get('state', 'N/A')}")
                    print(f"   Category: {result.get('category', 'N/A')}")
                else:
                    print("❌ Knowledge API: No results")
            else:
                print(f"❌ Knowledge API error: {response.status_code}")

if __name__ == "__main__":
    asyncio.run(test_debug())
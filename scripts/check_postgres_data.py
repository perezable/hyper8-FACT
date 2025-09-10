#!/usr/bin/env python3
"""
Check if data is actually in PostgreSQL on Railway.
"""

import json
import httpx
import asyncio

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

async def check_data():
    """Check data via different endpoints."""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check health endpoint
        print("=" * 60)
        print("Health Check")
        print("=" * 60)
        
        response = await client.get(f"{RAILWAY_URL}/health")
        if response.status_code == 200:
            data = response.json()
            metrics = data.get("metrics", {})
            print(f"Enhanced retriever entries: {metrics.get('enhanced_retriever_entries', 0)}")
        
        print()
        
        # Check knowledge search
        print("=" * 60)
        print("Knowledge Search API")
        print("=" * 60)
        
        response = await client.post(
            f"{RAILWAY_URL}/knowledge/search",
            json={"query": "Georgia", "limit": 1}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total results: {data['total_count']}")
            if data["results"]:
                result = data["results"][0]
                print(f"First result ID: {result['id']}")
                print(f"Question: {result['question']}")
                print(f"State: {result['state']}")
        
        print()
        
        # Get all entries
        print("=" * 60)
        print("Get All Knowledge Entries")
        print("=" * 60)
        
        response = await client.get(f"{RAILWAY_URL}/knowledge/entries")
        if response.status_code == 200:
            data = response.json()
            print(f"Total entries: {data['total_count']}")
            
            # Count by state
            state_counts = {}
            for entry in data["entries"]:
                state = entry.get("state", "N/A")
                state_counts[state] = state_counts.get(state, 0) + 1
            
            print("Entries by state:")
            for state, count in sorted(state_counts.items()):
                print(f"  {state}: {count}")

if __name__ == "__main__":
    asyncio.run(check_data())
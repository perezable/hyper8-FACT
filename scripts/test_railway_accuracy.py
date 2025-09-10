#!/usr/bin/env python3
"""
Test the Railway deployment to verify its accuracy and data.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

async def test_railway_knowledge():
    """Test knowledge retrieval on Railway deployment."""
    
    print("🧪 Testing Railway Knowledge Base")
    print("=" * 70)
    print(f"URL: {RAILWAY_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    print()
    
    async with aiohttp.ClientSession() as session:
        # 1. Check health
        print("1️⃣ Health Check:")
        async with session.get(f"{RAILWAY_URL}/health") as response:
            health = await response.json()
            print(f"   Status: {health['status']}")
            print(f"   Initialized: {health['initialized']}")
            print()
        
        # 2. Count total entries
        print("2️⃣ Total Knowledge Entries:")
        async with session.post(
            f"{RAILWAY_URL}/knowledge/search",
            json={"query": "", "limit": 1000}
        ) as response:
            data = await response.json()
            total = data.get('total_count', 0)
            print(f"   Found: {total} entries")
            
            if data.get('results'):
                # Get category breakdown
                categories = {}
                states = {}
                for entry in data['results']:
                    cat = entry.get('category', 'unknown')
                    categories[cat] = categories.get(cat, 0) + 1
                    if entry.get('state'):
                        state = entry['state']
                        states[state] = states.get(state, 0) + 1
                
                print(f"\n   Categories:")
                for cat, count in sorted(categories.items()):
                    print(f"     • {cat}: {count}")
                
                if states:
                    print(f"\n   States:")
                    for state, count in sorted(states.items()):
                        print(f"     • {state}: {count}")
        
        # 3. Test specific queries
        print("\n3️⃣ Test Queries:")
        test_queries = [
            ("California contractor license requirements", "CA"),
            ("Georgia contractor license requirements", "GA"),
            ("exam preparation tips", None),
            ("surety bond requirements", None),
            ("What happens if I fail the exam?", None)
        ]
        
        passed = 0
        failed = 0
        
        for query, expected_state in test_queries:
            print(f"\n   Query: '{query}'")
            async with session.post(
                f"{RAILWAY_URL}/knowledge/search",
                json={"query": query, "limit": 1}
            ) as response:
                data = await response.json()
                if data.get('results'):
                    result = data['results'][0]
                    print(f"   ✓ Found: {result['question'][:60]}...")
                    if expected_state:
                        actual_state = result.get('state', 'None')
                        if actual_state == expected_state:
                            print(f"   ✓ State match: {actual_state}")
                            passed += 1
                        else:
                            print(f"   ✗ State mismatch: Expected {expected_state}, got {actual_state}")
                            failed += 1
                    else:
                        passed += 1
                else:
                    print(f"   ✗ No results found")
                    failed += 1
        
        # 4. Calculate accuracy
        total_tests = passed + failed
        if total_tests > 0:
            accuracy = (passed / total_tests) * 100
            print(f"\n4️⃣ Accuracy Results:")
            print(f"   Passed: {passed}/{total_tests}")
            print(f"   Failed: {failed}/{total_tests}")
            print(f"   Accuracy: {accuracy:.1f}%")
        
        # 5. Performance test
        print(f"\n5️⃣ Performance Test:")
        start = datetime.now()
        tasks = []
        for i in range(10):
            task = session.post(
                f"{RAILWAY_URL}/knowledge/search",
                json={"query": f"test query {i}", "limit": 1}
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        end = datetime.now()
        
        total_time = (end - start).total_seconds()
        avg_time = total_time / 10 * 1000  # Convert to ms
        print(f"   10 concurrent requests: {total_time:.2f}s")
        print(f"   Average response time: {avg_time:.1f}ms")
        
        [r.close() for r in responses]
    
    print("\n" + "=" * 70)
    print("📊 Summary:")
    print(f"   Data Status: {total} entries loaded")
    if total < 100:
        print("   ⚠️  Very limited data - not the 450 entries from 96.7% test")
        print("   ⚠️  This is test/mock data, not the actual knowledge base")
    elif total >= 400:
        print("   ✅ Full knowledge base loaded (450 entries expected)")
    else:
        print(f"   ⚠️  Partial data loaded ({total}/450 expected)")

if __name__ == "__main__":
    asyncio.run(test_railway_knowledge())
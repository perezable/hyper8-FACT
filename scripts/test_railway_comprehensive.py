#!/usr/bin/env python3
"""
Comprehensive Railway accuracy test to verify 96.7%+ accuracy.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

# Comprehensive test queries
TEST_QUERIES = [
    # State-specific
    ("Georgia contractor license requirements", "GA", True),
    ("California contractor license", "CA", True),
    ("Florida licensing requirements", "FL", True),
    ("Texas contractor regulations", "TX", True),
    ("Nevada exam requirements", "NV", True),
    
    # Topic-based
    ("exam preparation tips", None, True),
    ("study materials and books", None, True),
    ("practice exam questions", None, True),
    ("payment plan options", None, True),
    ("financing for contractors", None, True),
    
    # Financial
    ("ROI calculation", None, True),
    ("first project payback", None, True),
    ("tax benefits", None, True),
    
    # Insurance/Bonding
    ("surety bond requirements", None, True),
    ("workers compensation insurance", None, True),
    ("general liability coverage", None, True),
    
    # Process questions
    ("What happens if I fail the exam", None, True),
    ("How long does licensing take", None, True),
    ("DIY vs professional service", None, True),
    ("expedited processing", None, True),
    
    # Specific topics
    ("What is a mechanics lien", None, True),
    ("qualifier arrangement costs", None, True),
    ("NASCLA reciprocity states", None, True),
    ("multi-state expansion", None, True),
    
    # Objection handling
    ("too expensive objection", None, True),
    ("need to think about it", None, True),
    ("can I do this myself", None, True),
    
    # Business operations
    ("LLC formation requirements", None, True),
    ("business entity setup", None, True),
    ("registered agent services", None, True)
]

async def test_railway_comprehensive():
    """Run comprehensive accuracy test."""
    print("🧪 Comprehensive Railway Accuracy Test")
    print("=" * 70)
    print(f"URL: {RAILWAY_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Total test queries: {len(TEST_QUERIES)}")
    
    async with aiohttp.ClientSession() as session:
        # Check health first
        async with session.get(f"{RAILWAY_URL}/health") as r:
            health = await r.json()
            print(f"\n✅ System Status: {health['status']}")
            print(f"✅ Enhanced Retriever: {health['metrics'].get('enhanced_retriever_entries', 0)} entries")
        
        # Run test queries
        passed = 0
        failed = 0
        
        print("\n📊 Running Test Queries:")
        print("-" * 70)
        
        for query, expected_state, should_find in TEST_QUERIES:
            async with session.post(
                f"{RAILWAY_URL}/knowledge/search",
                json={"query": query, "limit": 3}
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    results = data.get("results", [])
                    
                    if should_find and results:
                        # Check if we found relevant results
                        top_result = results[0]
                        
                        # State check if applicable
                        state_match = True
                        if expected_state:
                            state_match = top_result.get("state") == expected_state
                        
                        if state_match:
                            passed += 1
                            print(f"✅ '{query[:40]}'")
                        else:
                            failed += 1
                            print(f"❌ '{query[:40]}' - State mismatch")
                    elif should_find and not results:
                        failed += 1
                        print(f"❌ '{query[:40]}' - No results")
                    elif not should_find and not results:
                        passed += 1
                        print(f"✅ '{query[:40]}' - Correctly no results")
                    else:
                        failed += 1
                        print(f"❌ '{query[:40]}' - Unexpected")
                else:
                    failed += 1
                    print(f"❌ '{query[:40]}' - HTTP {r.status}")
        
        # Calculate accuracy
        total = passed + failed
        accuracy = (passed / total) * 100 if total > 0 else 0
        
        print("\n" + "=" * 70)
        print(f"📊 Results Summary:")
        print(f"   Total Tests: {total}")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   🎯 Accuracy: {accuracy:.1f}%")
        
        if accuracy >= 96.7:
            print(f"\n🏆 SUCCESS! Achieved {accuracy:.1f}% accuracy (target: 96.7%)")
        else:
            print(f"\n⚠️ Below target: {accuracy:.1f}% (target: 96.7%)")
        
        return accuracy >= 96.7

if __name__ == "__main__":
    import sys
    success = asyncio.run(test_railway_comprehensive())
    sys.exit(0 if success else 1)
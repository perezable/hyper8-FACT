#!/usr/bin/env python3
"""
Final test of Railway with enhanced retriever fix.
Should achieve close to 96.7% accuracy like local system.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

async def wait_and_test():
    """Wait for deployment and test enhanced search."""
    print("🚀 Railway Enhanced Retriever Test")
    print("=" * 70)
    
    # Wait a bit for deployment
    print("⏳ Waiting 60s for Railway deployment...")
    await asyncio.sleep(60)
    
    async with aiohttp.ClientSession() as session:
        # Check health
        print("\n📊 Checking deployment...")
        async with session.get(f"{RAILWAY_URL}/health") as r:
            health = await r.json()
            print(f"Status: {health['status']}")
            print(f"Initialized: {health['initialized']}")
        
        # Check data count
        async with session.post(
            f"{RAILWAY_URL}/knowledge/search",
            json={"query": "", "limit": 500}
        ) as r:
            data = await r.json()
            count = len(data.get('results', []))
            print(f"Knowledge entries: {count}")
            
            if count < 400:
                # Re-upload data if needed
                print("\n📚 Re-uploading knowledge base...")
                kb_data = json.load(open('data/knowledge_export.json'))['knowledge_base']
                
                for i in range(0, len(kb_data), 50):
                    chunk = kb_data[i:i+50]
                    upload = {
                        'data_type': 'knowledge_base',
                        'data': chunk,
                        'clear_existing': (i == 0)
                    }
                    try:
                        async with session.post(
                            f"{RAILWAY_URL}/upload-data",
                            json=upload,
                            timeout=aiohttp.ClientTimeout(total=15)
                        ) as r:
                            if r.status == 200:
                                print(".", end="", flush=True)
                    except:
                        print("x", end="", flush=True)
                    await asyncio.sleep(0.1)
                print("\n✅ Upload complete")
        
        # Test enhanced search
        print("\n🧪 Testing Enhanced Search...")
        test_queries = [
            ("California contractor license requirements", "state_licensing"),
            ("exam preparation tips", "exam_preparation"),
            ("How do I get a surety bond?", "insurance_bonding"),
            ("too expensive objection", "objection_handling"),
            ("What happens if I fail the exam?", "troubleshooting"),
            ("success stories from contractors", "success_stories"),
            ("qualifier network info", "qualifier_network"),
            ("business formation steps", "business_formation"),
            ("regulatory updates 2025", "regulatory"),
            ("ROI on contractor license", "financial_planning")
        ]
        
        passed = 0
        total_time = 0
        
        print("\nRunning test queries:")
        print("-" * 50)
        
        for query, expected_substr in test_queries:
            start = time.time()
            
            async with session.post(
                f"{RAILWAY_URL}/knowledge/search",
                json={"query": query, "limit": 3}
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    elapsed = (time.time() - start) * 1000
                    total_time += elapsed
                    
                    if data.get('results'):
                        result = data['results'][0]
                        category = result.get('category', '')
                        
                        if expected_substr in category:
                            passed += 1
                            print(f"✅ {query[:40]:40} [{elapsed:5.1f}ms]")
                        else:
                            print(f"❌ {query[:40]:40} [{elapsed:5.1f}ms]")
                            print(f"   Expected: {expected_substr} in category")
                            print(f"   Got: {category}")
                    else:
                        print(f"❌ {query[:40]:40} - No results")
                else:
                    print(f"❌ {query[:40]:40} - HTTP {r.status}")
        
        # Results
        accuracy = (passed / len(test_queries)) * 100
        avg_time = total_time / len(test_queries)
        
        print("\n" + "=" * 70)
        print("📊 RESULTS")
        print("=" * 70)
        print(f"Accuracy: {accuracy:.1f}% ({passed}/{len(test_queries)} passed)")
        print(f"Average Response Time: {avg_time:.1f}ms")
        print(f"Knowledge Entries: {count}")
        
        if accuracy >= 90:
            print("\n🎉 SUCCESS! Railway matches local performance!")
            print("   Enhanced retriever is working correctly")
        elif accuracy >= 70:
            print("\n✅ Good performance with enhanced retriever")
        elif accuracy >= 50:
            print("\n⚠️  Partial improvement with enhanced retriever")
        else:
            print("\n❌ Enhanced retriever may not be working")
        
        print(f"\nComparison:")
        print(f"  Railway: {accuracy:.1f}%")
        print(f"  Local: 96.7%")
        print(f"  Difference: {accuracy - 96.7:+.1f}%")

asyncio.run(wait_and_test())
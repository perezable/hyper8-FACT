#!/usr/bin/env python3
"""
Test Objection Handling Deployment
Verify that objection handling entries are properly deployed and functional
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, List

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

async def test_objection_responses():
    """Test that objection handling responses work correctly"""
    
    test_queries = [
        "I can do this myself for free",
        "Other companies charge less",
        "I don't trust online services", 
        "I need to talk to my spouse first",
        "Why not just use a handyman",
        "This isn't urgent",
        "What if you mess something up",
        "Never heard of your company",
        "Cannot afford it right now"
    ]
    
    results = {
        "total_tests": len(test_queries),
        "successful_responses": 0,
        "sarah_responses": 0,
        "michael_responses": 0,
        "failed_queries": [],
        "response_details": []
    }
    
    async with aiohttp.ClientSession() as session:
        for query in test_queries:
            try:
                # Test the query endpoint
                async with session.post(
                    f"{RAILWAY_URL}/query",
                    json={"query": query, "category": "objection_handling"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('answer'):
                            results["successful_responses"] += 1
                            answer = data.get('answer', '')
                            
                            # Check for response styles
                            if 'Sarah:' in answer:
                                results["sarah_responses"] += 1
                            elif 'Michael:' in answer:
                                results["michael_responses"] += 1
                            
                            results["response_details"].append({
                                "query": query,
                                "answer_preview": answer[:100] + "..." if len(answer) > 100 else answer,
                                "category": data.get('category'),
                                "tags": data.get('tags'),
                                "personas": data.get('personas')
                            })
                            
                            print(f"✅ {query[:30]}... -> {'Sarah' if 'Sarah:' in answer else 'Michael' if 'Michael:' in answer else 'Unknown'}")
                        else:
                            results["failed_queries"].append(query)
                            print(f"❌ {query[:30]}... -> No answer")
                    else:
                        results["failed_queries"].append(query)
                        print(f"❌ {query[:30]}... -> HTTP {response.status}")
                        
            except Exception as e:
                results["failed_queries"].append(query)
                print(f"❌ {query[:30]}... -> Error: {e}")
    
    return results

async def test_database_stats():
    """Get database statistics"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{RAILWAY_URL}/api/knowledge-stats",
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}"}
                    
    except Exception as e:
        return {"error": str(e)}

async def test_objection_search():
    """Test searching specifically for objection handling entries"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{RAILWAY_URL}/search",
                json={
                    "query": "objection_handling",
                    "category": "objection_handling",
                    "limit": 30
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return {
                        "total_found": len(data.get('results', [])),
                        "results": data.get('results', [])
                    }
                else:
                    return {"error": f"HTTP {response.status}"}
                    
    except Exception as e:
        return {"error": str(e)}

async def main():
    """Main test execution"""
    print("🧪 Testing Objection Handling Deployment")
    print("=" * 50)
    
    # Test 1: Database stats
    print("\n📊 Database Statistics:")
    stats = await test_database_stats()
    if "error" not in stats:
        print(f"   Total Entries: {stats.get('total_entries', 'N/A')}")
        print(f"   Categories: {len(stats.get('categories', []))}")
        print(f"   Last Updated: {stats.get('last_updated', 'N/A')}")
    else:
        print(f"   ❌ Error: {stats['error']}")
    
    # Test 2: Objection search
    print("\n🔍 Objection Handling Search:")
    search_results = await test_objection_search()
    if "error" not in search_results:
        print(f"   Found {search_results['total_found']} objection handling entries")
        if search_results['total_found'] > 0:
            # Show a few examples
            for i, result in enumerate(search_results['results'][:3]):
                question = result.get('question', 'N/A')
                tags = result.get('tags', 'N/A')
                print(f"   {i+1}. {question[:40]}... (tags: {tags})")
    else:
        print(f"   ❌ Error: {search_results['error']}")
    
    # Test 3: Response testing
    print("\n🎯 Testing Objection Responses:")
    response_results = await test_objection_responses()
    
    print(f"\n📈 Test Results Summary:")
    print(f"   Total Tests: {response_results['total_tests']}")
    print(f"   Successful Responses: {response_results['successful_responses']}")
    print(f"   Sarah Responses: {response_results['sarah_responses']}")
    print(f"   Michael Responses: {response_results['michael_responses']}")
    print(f"   Failed Queries: {len(response_results['failed_queries'])}")
    
    if response_results['failed_queries']:
        print(f"\n❌ Failed Queries:")
        for query in response_results['failed_queries']:
            print(f"   - {query}")
    
    # Calculate success rate
    success_rate = (response_results['successful_responses'] / response_results['total_tests']) * 100
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    # Style balance check
    total_styled = response_results['sarah_responses'] + response_results['michael_responses']
    if total_styled > 0:
        sarah_pct = (response_results['sarah_responses'] / total_styled) * 100
        michael_pct = (response_results['michael_responses'] / total_styled) * 100
        print(f"📊 Style Distribution: Sarah {sarah_pct:.1f}%, Michael {michael_pct:.1f}%")
    
    # Overall assessment
    print("\n" + "=" * 50)
    if success_rate >= 80 and response_results['sarah_responses'] > 0 and response_results['michael_responses'] > 0:
        print("🎉 DEPLOYMENT VERIFICATION: ✅ SUCCESS")
        print("   • Objection handling responses are working correctly")
        print("   • Both Sarah and Michael response styles are present")
        print("   • High success rate achieved")
        return 0
    else:
        print("⚠️  DEPLOYMENT VERIFICATION: ❌ ISSUES DETECTED")
        if success_rate < 80:
            print(f"   • Low success rate: {success_rate:.1f}% (expected >80%)")
        if response_results['sarah_responses'] == 0:
            print("   • No Sarah-style responses found")
        if response_results['michael_responses'] == 0:
            print("   • No Michael-style responses found")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
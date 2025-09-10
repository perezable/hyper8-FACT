#!/usr/bin/env python3
"""
Full test of Railway deployment with complete knowledge base.
This runs the same enhanced test that achieved 96.7% accuracy locally.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

async def wait_for_deployment():
    """Wait for Railway to deploy the search limit fix."""
    print("⏳ Waiting for Railway deployment with search limit fix...")
    
    async with aiohttp.ClientSession() as session:
        for i in range(20):  # Wait up to ~3 minutes
            try:
                # Check if we can get more than 100 results
                async with session.post(
                    f"{RAILWAY_URL}/knowledge/search",
                    json={"query": "", "limit": 500},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        count = data.get('total_count', 0)
                        results_len = len(data.get('results', []))
                        
                        # If we can get more than 100 results, the fix is deployed
                        if results_len > 100 or count > 100:
                            print(f"✅ Deployment ready! Can retrieve {results_len} results")
                            return True
                        elif i % 3 == 0:
                            print(f"   Still limited to {results_len} results, waiting...")
            except:
                pass
            
            await asyncio.sleep(10)
    
    return False

async def upload_all_data():
    """Upload the complete 450-entry knowledge base."""
    print("\n📚 Uploading Complete Knowledge Base")
    print("=" * 70)
    
    # Load the exported data
    with open('data/knowledge_export.json', 'r') as f:
        export_data = json.load(f)
    
    entries = export_data['knowledge_base']
    print(f"Loaded {len(entries)} entries to upload")
    
    async with aiohttp.ClientSession() as session:
        # Upload in chunks
        chunk_size = 25
        chunks = [entries[i:i+chunk_size] for i in range(0, len(entries), chunk_size)]
        
        total_uploaded = 0
        print(f"Uploading in {len(chunks)} chunks...")
        
        for i, chunk in enumerate(chunks, 1):
            if i % 5 == 1:
                print(f"  Progress: {i}/{len(chunks)} chunks...")
            
            upload_data = {
                "data_type": "knowledge_base",
                "data": chunk,
                "clear_existing": (i == 1)  # Clear on first chunk
            }
            
            try:
                async with session.post(
                    f"{RAILWAY_URL}/upload-data",
                    json=upload_data,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        total_uploaded += result.get('records_uploaded', len(chunk))
            except:
                pass
            
            await asyncio.sleep(0.1)
        
        print(f"✅ Uploaded {total_uploaded} entries")
        
        # Verify count
        async with session.post(
            f"{RAILWAY_URL}/knowledge/search",
            json={"query": "", "limit": 1000}
        ) as response:
            data = await response.json()
            actual_count = len(data.get('results', []))
            print(f"✅ Railway now has {actual_count} searchable entries")
            return actual_count

async def run_enhanced_test():
    """Run the enhanced test that achieved 96.7% accuracy locally."""
    print("\n🧪 Running Enhanced Knowledge Base Test")
    print("=" * 70)
    
    # Test queries with variations
    test_cases = [
        # Original queries
        ("What are the requirements for a California contractor license?", "state_licensing_requirements"),
        ("How much does a contractor license cost in Georgia?", "state_licensing_requirements"),
        ("What is the PSI exam?", "exam_preparation_testing"),
        ("How do I prepare for the contractor exam?", "exam_preparation_testing"),
        ("What happens if I fail the contractor exam?", "troubleshooting_problem_resolution"),
        
        # Variations with typos and casual language
        ("california contractors licence requirments", "state_licensing_requirements"),
        ("GA license costs", "state_licensing_requirements"),
        ("whats PSI exam", "exam_preparation_testing"),
        ("exam prep tips", "exam_preparation_testing"),
        ("failed the test what now", "troubleshooting_problem_resolution"),
        
        # Business and financial queries
        ("How do I get a surety bond?", "insurance_bonding"),
        ("What's the ROI on getting licensed?", "financial_planning_roi"),
        ("How to handle 'too expensive' objection", "objection_handling_scripts"),
        ("Success stories from contractors", "success_stories_case_studies"),
        ("Qualifier network programs info", "qualifier_network_programs"),
    ]
    
    async with aiohttp.ClientSession() as session:
        passed = 0
        failed = 0
        total_time = 0
        
        print(f"Running {len(test_cases)} test queries...\n")
        
        for query, expected_category in test_cases:
            start = time.time()
            
            try:
                async with session.post(
                    f"{RAILWAY_URL}/knowledge/search",
                    json={"query": query, "limit": 3},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        elapsed = (time.time() - start) * 1000  # Convert to ms
                        total_time += elapsed
                        
                        if data.get('results'):
                            result = data['results'][0]
                            actual_category = result.get('category', 'unknown')
                            
                            if actual_category == expected_category:
                                passed += 1
                                print(f"✅ PASS: '{query[:40]}...'")
                                print(f"   Found: {result['question'][:50]}...")
                                print(f"   Time: {elapsed:.1f}ms")
                            else:
                                failed += 1
                                print(f"❌ FAIL: '{query[:40]}...'")
                                print(f"   Expected: {expected_category}")
                                print(f"   Got: {actual_category}")
                        else:
                            failed += 1
                            print(f"❌ FAIL: '{query[:40]}...' - No results")
                    else:
                        failed += 1
                        print(f"❌ FAIL: '{query[:40]}...' - HTTP {response.status}")
            except Exception as e:
                failed += 1
                print(f"❌ FAIL: '{query[:40]}...' - Error: {e}")
            
            print()
        
        # Calculate metrics
        total = passed + failed
        accuracy = (passed / total * 100) if total > 0 else 0
        avg_time = total_time / total if total > 0 else 0
        
        print("=" * 70)
        print("📊 TEST RESULTS")
        print("=" * 70)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Accuracy: {accuracy:.1f}%")
        print(f"Average Response Time: {avg_time:.1f}ms")
        
        if accuracy >= 90:
            print("\n🎉 EXCELLENT! Railway matches local performance!")
            grade = "A+"
        elif accuracy >= 80:
            print("\n✅ GOOD performance on Railway")
            grade = "B"
        elif accuracy >= 70:
            print("\n⚠️  FAIR performance on Railway")
            grade = "C"
        else:
            print("\n❌ POOR performance on Railway")
            grade = "F"
        
        print(f"Grade: {grade}")
        
        return accuracy

async def main():
    """Main test execution."""
    print("🚀 Railway Full Test Suite")
    print("=" * 70)
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Target: {RAILWAY_URL}")
    
    # Wait for deployment
    if not await wait_for_deployment():
        print("\n⚠️  Deployment not ready or limit not fixed")
        print("Continuing with current deployment...")
    
    # Upload all data
    count = await upload_all_data()
    
    if count < 400:
        print(f"\n⚠️  Warning: Only {count} entries loaded (expected 450)")
        print("Test results may not match local 96.7% accuracy")
    
    # Run enhanced test
    accuracy = await run_enhanced_test()
    
    print("\n" + "=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    print(f"Railway Entries: {count}")
    print(f"Test Accuracy: {accuracy:.1f}%")
    
    if accuracy >= 95 and count >= 400:
        print("\n✅ Railway deployment successfully matches local system!")
        print("   Both systems achieve ~96.7% accuracy with 450 entries")
    else:
        print(f"\n⚠️  Railway performance: {accuracy:.1f}% vs Local: 96.7%")
        if count < 400:
            print(f"   Limited by entry count: {count} vs 450")

if __name__ == "__main__":
    asyncio.run(main())
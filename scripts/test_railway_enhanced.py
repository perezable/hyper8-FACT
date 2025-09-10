#!/usr/bin/env python3
"""
Enhanced test for Railway deployment.
Tests the same queries that achieved 96.7% accuracy locally.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import List, Dict, Tuple

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

# Test queries from the original 96.7% test
TEST_QUERIES = [
    # State licensing
    ("What are the requirements for a California contractor license?", "state_licensing_requirements"),
    ("California contractor license requirements", "state_licensing_requirements"),
    ("CA contractor licensing", "state_licensing_requirements"),
    ("california contractors licence requirments", "state_licensing_requirements"),  # With typos
    
    # Exam preparation
    ("How do I prepare for the contractor exam?", "exam_preparation_testing"),
    ("exam preparation tips", "exam_preparation_testing"),
    ("contractor test prep", "exam_preparation_testing"),
    ("PSI exam information", "exam_preparation_testing"),
    
    # Insurance and bonding
    ("How do I get a surety bond?", "insurance_bonding"),
    ("surety bond requirements", "insurance_bonding"),
    ("contractor bond costs", "insurance_bonding"),
    
    # Financial planning
    ("What's the ROI on getting licensed?", "financial_planning_roi"),
    ("contractor license ROI", "financial_planning_roi"),
    ("is contractor license worth it", "financial_planning_roi"),
    
    # Objection handling
    ("How to handle too expensive objection", "objection_handling_scripts"),
    ("objection handling scripts", "objection_handling_scripts"),
    ("customer says too expensive", "objection_handling_scripts"),
    
    # Troubleshooting
    ("What happens if I fail the contractor exam?", "troubleshooting_problem_resolution"),
    ("failed contractor test what now", "troubleshooting_problem_resolution"),
    ("exam failure next steps", "troubleshooting_problem_resolution"),
    
    # Success stories
    ("Success stories from contractors", "success_stories_case_studies"),
    ("contractor success examples", "success_stories_case_studies"),
    
    # Business formation
    ("How to start a contracting business", "business_formation_operations"),
    ("business formation steps", "business_formation_operations"),
    
    # Qualifier network
    ("Qualifier network programs info", "qualifier_network_programs"),
    ("what is qualifier network", "qualifier_network_programs"),
    
    # Regulatory updates
    ("Latest regulatory changes", "regulatory_updates_compliance"),
    ("2025 regulation updates", "regulatory_updates_compliance"),
]

async def test_railway_search(session: aiohttp.ClientSession, query: str, expected_category: str) -> Dict:
    """Test a single search query."""
    start = time.time()
    
    try:
        async with session.post(
            f"{RAILWAY_URL}/knowledge/search",
            json={"query": query, "limit": 3},
            timeout=aiohttp.ClientTimeout(total=5)
        ) as response:
            if response.status == 200:
                data = await response.json()
                elapsed = (time.time() - start) * 1000
                
                if data.get('results'):
                    result = data['results'][0]
                    actual_category = result.get('category', 'unknown')
                    
                    return {
                        'query': query,
                        'expected': expected_category,
                        'actual': actual_category,
                        'passed': actual_category == expected_category,
                        'question_found': result.get('question', ''),
                        'answer_preview': result.get('answer', '')[:100],
                        'time_ms': elapsed,
                        'found': True
                    }
                else:
                    return {
                        'query': query,
                        'expected': expected_category,
                        'actual': None,
                        'passed': False,
                        'time_ms': elapsed,
                        'found': False
                    }
            else:
                return {
                    'query': query,
                    'expected': expected_category,
                    'passed': False,
                    'error': f'HTTP {response.status}',
                    'time_ms': (time.time() - start) * 1000
                }
    except Exception as e:
        return {
            'query': query,
            'expected': expected_category,
            'passed': False,
            'error': str(e),
            'time_ms': (time.time() - start) * 1000
        }

async def run_railway_test():
    """Run the complete test suite."""
    print("🚀 RAILWAY ENHANCED KNOWLEDGE BASE TEST")
    print("=" * 70)
    print(f"URL: {RAILWAY_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    
    async with aiohttp.ClientSession() as session:
        # Check current data
        print("\n📊 Checking Railway Data...")
        async with session.post(
            f"{RAILWAY_URL}/knowledge/search",
            json={"query": "", "limit": 1000}
        ) as response:
            data = await response.json()
            total_entries = len(data.get('results', []))
            print(f"Total entries: {total_entries}")
            
            if total_entries < 400:
                print(f"⚠️  Warning: Only {total_entries} entries (expected 450)")
        
        # Run all tests
        print(f"\n🧪 Running {len(TEST_QUERIES)} test queries...")
        print("-" * 70)
        
        results = []
        for query, expected in TEST_QUERIES:
            result = await test_railway_search(session, query, expected)
            results.append(result)
            
            # Print result
            if result.get('passed'):
                print(f"✅ PASS: {query[:50]}")
                print(f"   Time: {result['time_ms']:.1f}ms")
            else:
                print(f"❌ FAIL: {query[:50]}")
                if result.get('found'):
                    print(f"   Expected: {expected}")
                    print(f"   Got: {result.get('actual')}")
                elif result.get('error'):
                    print(f"   Error: {result['error']}")
                else:
                    print(f"   No results found")
        
        # Calculate metrics
        passed = sum(1 for r in results if r.get('passed'))
        failed = len(results) - passed
        accuracy = (passed / len(results)) * 100
        
        # Performance metrics
        valid_times = [r['time_ms'] for r in results if 'time_ms' in r and not r.get('error')]
        avg_time = sum(valid_times) / len(valid_times) if valid_times else 0
        
        # Category accuracy
        category_stats = {}
        for result in results:
            cat = result['expected']
            if cat not in category_stats:
                category_stats[cat] = {'passed': 0, 'total': 0}
            category_stats[cat]['total'] += 1
            if result.get('passed'):
                category_stats[cat]['passed'] += 1
        
        print("\n" + "=" * 70)
        print("📈 TEST RESULTS")
        print("=" * 70)
        
        print(f"\n📊 Overall Metrics:")
        print(f"   Total Tests: {len(results)}")
        print(f"   Passed: {passed}")
        print(f"   Failed: {failed}")
        print(f"   Accuracy: {accuracy:.1f}%")
        print(f"   Avg Response Time: {avg_time:.1f}ms")
        
        print(f"\n📂 Category Performance:")
        for cat, stats in sorted(category_stats.items()):
            cat_accuracy = (stats['passed'] / stats['total']) * 100
            print(f"   {cat}: {cat_accuracy:.0f}% ({stats['passed']}/{stats['total']})")
        
        # Grade
        if accuracy >= 95:
            grade = "A+"
            assessment = "EXCELLENT - Matches local performance!"
        elif accuracy >= 85:
            grade = "A"
            assessment = "VERY GOOD"
        elif accuracy >= 75:
            grade = "B"
            assessment = "GOOD"
        elif accuracy >= 65:
            grade = "C"
            assessment = "SATISFACTORY"
        else:
            grade = "F"
            assessment = "NEEDS IMPROVEMENT"
        
        print(f"\n🎯 Final Grade: {grade} ({assessment})")
        
        # Compare to local
        print(f"\n📋 Comparison:")
        print(f"   Railway: {accuracy:.1f}%")
        print(f"   Local: 96.7%")
        print(f"   Difference: {accuracy - 96.7:+.1f}%")
        
        if accuracy >= 90:
            print("\n✅ SUCCESS! Railway deployment matches local system performance!")
        elif accuracy >= 70:
            print("\n⚠️  Railway performance is acceptable but below local system")
        else:
            print("\n❌ Railway performance needs improvement")
        
        return accuracy

if __name__ == "__main__":
    accuracy = asyncio.run(run_railway_test())
    exit(0 if accuracy >= 90 else 1)
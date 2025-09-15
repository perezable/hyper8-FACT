#!/usr/bin/env python3
"""
Comprehensive Scored Test of FACT System with Groq API
Evaluates accuracy, relevance, and performance
"""

import asyncio
import json
import time
import requests
from typing import Dict, List, Any, Tuple
from datetime import datetime
import re

# Test configuration
API_URL = "https://hyper8-fact-fact-system.up.railway.app"
TEST_TIMEOUT = 30
RATE_LIMIT_DELAY = 2.1  # Respect 30 requests/minute limit

# Comprehensive test cases with expected keywords for scoring
TEST_CASES = [
    {
        "query": "What is the NASCLA certification?",
        "category": "Basic Information",
        "expected_keywords": ["National Association", "contractor", "licensing", "certification", "states", "reciprocity"],
        "expected_topics": ["multi-state", "exam", "requirements"],
        "weight": 1.0
    },
    {
        "query": "Which states accept NASCLA certification?",
        "category": "State Recognition",
        "expected_keywords": ["states", "Alabama", "Arkansas", "Louisiana", "Mississippi", "Tennessee"],
        "expected_topics": ["reciprocity", "acceptance", "recognition"],
        "weight": 1.0
    },
    {
        "query": "How much does a Florida contractor license cost?",
        "category": "Cost Information",
        "expected_keywords": ["Florida", "cost", "fee", "dollar", "$", "application", "exam"],
        "expected_topics": ["price", "payment", "expense"],
        "weight": 1.0
    },
    {
        "query": "What are the steps to get a general contractor license in Texas?",
        "category": "Process Information",
        "expected_keywords": ["Texas", "steps", "application", "exam", "experience", "requirements"],
        "expected_topics": ["process", "procedure", "qualification"],
        "weight": 1.5
    },
    {
        "query": "What is the minimum net worth requirement for a Florida contractor?",
        "category": "Financial Requirements",
        "expected_keywords": ["Florida", "net worth", "financial", "minimum", "requirement"],
        "expected_topics": ["assets", "financial statement", "bonding"],
        "weight": 1.2
    },
    {
        "query": "How long is a contractor license valid in Georgia?",
        "category": "License Duration",
        "expected_keywords": ["Georgia", "valid", "years", "renewal", "expiration"],
        "expected_topics": ["duration", "period", "term"],
        "weight": 1.0
    },
    {
        "query": "What types of work require a specialty contractor license?",
        "category": "License Types",
        "expected_keywords": ["specialty", "electrical", "plumbing", "HVAC", "roofing", "types"],
        "expected_topics": ["classification", "categories", "specialized"],
        "weight": 1.3
    },
    {
        "query": "Can I work in multiple states with one license?",
        "category": "Reciprocity",
        "expected_keywords": ["multiple", "states", "reciprocity", "NASCLA", "agreement"],
        "expected_topics": ["interstate", "transfer", "recognition"],
        "weight": 1.2
    },
    {
        "query": "What happens if my contractor license expires?",
        "category": "Compliance",
        "expected_keywords": ["expire", "renewal", "penalty", "grace period", "reinstate"],
        "expected_topics": ["consequences", "violation", "inactive"],
        "weight": 1.1
    },
    {
        "query": "What are the insurance requirements for contractors in California?",
        "category": "Insurance Requirements",
        "expected_keywords": ["California", "insurance", "liability", "workers compensation", "bond"],
        "expected_topics": ["coverage", "policy", "minimum"],
        "weight": 1.3
    },
    {
        "query": "How do I verify a contractor's license?",
        "category": "Verification",
        "expected_keywords": ["verify", "check", "license", "board", "website", "database"],
        "expected_topics": ["validation", "confirm", "lookup"],
        "weight": 1.0
    },
    {
        "query": "What is the difference between a general contractor and subcontractor license?",
        "category": "License Classification",
        "expected_keywords": ["general", "subcontractor", "difference", "scope", "authority"],
        "expected_topics": ["prime contractor", "specialty", "responsibility"],
        "weight": 1.4
    }
]

def calculate_keyword_score(response: str, test_case: Dict) -> Tuple[float, Dict]:
    """
    Calculate keyword matching score for a response.
    
    Returns:
        Tuple of (score, details)
    """
    response_lower = response.lower()
    
    # Check expected keywords (must have)
    keywords_found = []
    keywords_missing = []
    
    for keyword in test_case["expected_keywords"]:
        if keyword.lower() in response_lower:
            keywords_found.append(keyword)
        else:
            keywords_missing.append(keyword)
    
    # Check topic keywords (nice to have)
    topics_found = []
    for topic in test_case["expected_topics"]:
        if topic.lower() in response_lower:
            topics_found.append(topic)
    
    # Calculate scores
    keyword_score = len(keywords_found) / len(test_case["expected_keywords"]) if test_case["expected_keywords"] else 0
    topic_score = len(topics_found) / len(test_case["expected_topics"]) if test_case["expected_topics"] else 0
    
    # Weighted final score (70% keywords, 30% topics)
    final_score = (keyword_score * 0.7) + (topic_score * 0.3)
    
    return final_score, {
        "keywords_found": keywords_found,
        "keywords_missing": keywords_missing,
        "topics_found": topics_found,
        "keyword_coverage": f"{len(keywords_found)}/{len(test_case['expected_keywords'])}",
        "topic_coverage": f"{len(topics_found)}/{len(test_case['expected_topics'])}"
    }

def calculate_quality_score(response: str) -> Tuple[float, Dict]:
    """
    Calculate quality metrics for a response.
    
    Returns:
        Tuple of (score, details)
    """
    scores = {}
    
    # Length check (should be substantial)
    length = len(response)
    if length < 100:
        scores["length"] = 0.2
    elif length < 300:
        scores["length"] = 0.5
    elif length < 1000:
        scores["length"] = 0.8
    else:
        scores["length"] = 1.0
    
    # Structure check (paragraphs, lists, etc.)
    has_structure = False
    if "\n\n" in response or "\n•" in response or "\n-" in response or "\n1." in response:
        has_structure = True
        scores["structure"] = 1.0
    else:
        scores["structure"] = 0.5
    
    # Specificity check (contains numbers, specific terms)
    has_numbers = bool(re.search(r'\d+', response))
    has_dollars = "$" in response
    has_specifics = has_numbers or has_dollars
    scores["specificity"] = 1.0 if has_specifics else 0.5
    
    # Professional language check
    professional_terms = ["requirement", "application", "certification", "license", "regulation", 
                         "compliance", "qualified", "authorized", "jurisdiction"]
    prof_count = sum(1 for term in professional_terms if term in response.lower())
    scores["professionalism"] = min(1.0, prof_count / 3)
    
    # Calculate overall quality score
    quality_score = sum(scores.values()) / len(scores)
    
    return quality_score, {
        "length": length,
        "has_structure": has_structure,
        "has_specifics": has_specifics,
        "professional_terms": prof_count,
        "subscores": scores
    }

def make_api_request(query: str) -> Tuple[bool, str, float, int]:
    """
    Make a request to the FACT API.
    
    Returns:
        Tuple of (success, response_text, response_time_ms, status_code)
    """
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{API_URL}/query",
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=TEST_TIMEOUT
        )
        
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            return True, data.get("response", ""), response_time, response.status_code
        else:
            return False, response.text, response_time, response.status_code
            
    except requests.exceptions.Timeout:
        return False, "Timeout", TEST_TIMEOUT * 1000, 408
    except Exception as e:
        return False, str(e), 0, 500

def print_test_header():
    """Print test header"""
    print("\n" + "="*80)
    print("🎯 COMPREHENSIVE SCORED TEST - GROQ API INTEGRATION")
    print("="*80)
    print(f"API URL: {API_URL}")
    print(f"Model: openai/gpt-oss-120b (via Groq)")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Test Cases: {len(TEST_CASES)}")
    print(f"Rate Limit: 30 requests/minute")
    print("="*80 + "\n")

def print_category_header(category: str):
    """Print category header"""
    print(f"\n{'='*60}")
    print(f"📋 {category}")
    print(f"{'='*60}")

def run_comprehensive_test():
    """Run comprehensive test suite with scoring"""
    print_test_header()
    
    # Track results by category
    category_results = {}
    all_results = []
    
    print("🔄 Starting comprehensive test...\n")
    
    for idx, test_case in enumerate(TEST_CASES, 1):
        category = test_case["category"]
        
        # Print progress
        print(f"[{idx}/{len(TEST_CASES)}] Testing: {test_case['query'][:60]}...")
        
        # Make API request
        success, response, response_time, status_code = make_api_request(test_case["query"])
        
        # Calculate scores
        if success and response:
            keyword_score, keyword_details = calculate_keyword_score(response, test_case)
            quality_score, quality_details = calculate_quality_score(response)
            
            # Weight-adjusted total score
            weighted_score = ((keyword_score * 0.6) + (quality_score * 0.4)) * test_case["weight"]
            
            result = {
                "test_case": test_case,
                "success": True,
                "response": response[:500] + "..." if len(response) > 500 else response,
                "response_time": response_time,
                "keyword_score": keyword_score,
                "quality_score": quality_score,
                "weighted_score": weighted_score,
                "keyword_details": keyword_details,
                "quality_details": quality_details
            }
        else:
            result = {
                "test_case": test_case,
                "success": False,
                "response": response,
                "response_time": response_time,
                "keyword_score": 0,
                "quality_score": 0,
                "weighted_score": 0,
                "error": f"Status {status_code}: {response[:100]}"
            }
        
        # Store result
        all_results.append(result)
        
        if category not in category_results:
            category_results[category] = []
        category_results[category].append(result)
        
        # Rate limiting
        if idx < len(TEST_CASES):
            time.sleep(RATE_LIMIT_DELAY)
    
    # Print detailed results
    print("\n" + "="*80)
    print("📊 DETAILED RESULTS BY CATEGORY")
    print("="*80)
    
    for category, results in category_results.items():
        print_category_header(category)
        
        for result in results:
            query = result["test_case"]["query"]
            print(f"\n🔍 Query: {query}")
            
            if result["success"]:
                print(f"✅ Status: Success | ⏱️ Time: {result['response_time']:.0f}ms")
                print(f"📊 Scores:")
                print(f"   - Keyword Match: {result['keyword_score']:.1%}")
                print(f"   - Quality Score: {result['quality_score']:.1%}")
                print(f"   - Weighted Total: {result['weighted_score']:.2f}")
                
                if "keyword_details" in result:
                    details = result["keyword_details"]
                    print(f"   - Keywords: {details['keyword_coverage']} found")
                    if details["keywords_missing"]:
                        print(f"   - Missing: {', '.join(details['keywords_missing'][:3])}")
                    
                print(f"📝 Response Preview:")
                print(f"   {result['response'][:200]}...")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
    
    # Calculate overall scores
    print("\n" + "="*80)
    print("📈 OVERALL SCORING SUMMARY")
    print("="*80)
    
    successful_tests = [r for r in all_results if r["success"]]
    failed_tests = [r for r in all_results if not r["success"]]
    
    if successful_tests:
        avg_keyword_score = sum(r["keyword_score"] for r in successful_tests) / len(successful_tests)
        avg_quality_score = sum(r["quality_score"] for r in successful_tests) / len(successful_tests)
        avg_weighted_score = sum(r["weighted_score"] for r in successful_tests) / len(successful_tests)
        avg_response_time = sum(r["response_time"] for r in successful_tests) / len(successful_tests)
        
        print(f"\n📊 Test Statistics:")
        print(f"   - Total Tests: {len(TEST_CASES)}")
        print(f"   - Successful: {len(successful_tests)} ({len(successful_tests)/len(TEST_CASES):.1%})")
        print(f"   - Failed: {len(failed_tests)} ({len(failed_tests)/len(TEST_CASES):.1%})")
        
        print(f"\n🎯 Average Scores (Successful Tests):")
        print(f"   - Keyword Accuracy: {avg_keyword_score:.1%}")
        print(f"   - Response Quality: {avg_quality_score:.1%}")
        print(f"   - Weighted Overall: {avg_weighted_score:.2f}/1.00")
        
        print(f"\n⚡ Performance Metrics:")
        print(f"   - Average Response Time: {avg_response_time:.0f}ms")
        print(f"   - Fastest Response: {min(r['response_time'] for r in successful_tests):.0f}ms")
        print(f"   - Slowest Response: {max(r['response_time'] for r in successful_tests):.0f}ms")
        
        # Category breakdown
        print(f"\n📋 Category Performance:")
        for category, results in category_results.items():
            cat_successful = [r for r in results if r["success"]]
            if cat_successful:
                cat_avg = sum(r["weighted_score"] for r in cat_successful) / len(cat_successful)
                print(f"   - {category}: {cat_avg:.2f}/1.00")
        
        # Final grade
        print(f"\n" + "="*80)
        print("🏆 FINAL GRADE")
        print("="*80)
        
        overall_percentage = (avg_weighted_score / 1.0) * 100
        
        if overall_percentage >= 90:
            grade = "A"
            verdict = "EXCELLENT - System performing at high accuracy"
        elif overall_percentage >= 80:
            grade = "B"
            verdict = "GOOD - System working well with minor gaps"
        elif overall_percentage >= 70:
            grade = "C"
            verdict = "SATISFACTORY - System functional but needs improvement"
        elif overall_percentage >= 60:
            grade = "D"
            verdict = "BELOW AVERAGE - System has significant gaps"
        else:
            grade = "F"
            verdict = "FAILING - System not meeting requirements"
        
        print(f"\n   Grade: {grade} ({overall_percentage:.1f}%)")
        print(f"   {verdict}")
        
        # Specific recommendations
        print(f"\n💡 Recommendations:")
        
        if avg_keyword_score < 0.7:
            print("   - ⚠️ Low keyword accuracy suggests responses may be off-topic")
            print("     Consider: Improving system prompts for contractor licensing context")
        
        if avg_quality_score < 0.7:
            print("   - ⚠️ Low quality scores indicate responses lack detail")
            print("     Consider: Enhancing knowledge base with more specific information")
        
        if avg_response_time > 5000:
            print("   - ⚠️ Slow response times may impact user experience")
            print("     Consider: Optimizing query processing or caching")
        
        if len(failed_tests) > len(TEST_CASES) * 0.2:
            print("   - ⚠️ High failure rate indicates system instability")
            print("     Consider: Investigating error handling and retry logic")
            
    else:
        print("\n❌ All tests failed - unable to calculate scores")
        print("System appears to be non-functional")
    
    print("="*80)
    
    return {
        "total_tests": len(TEST_CASES),
        "successful": len(successful_tests),
        "failed": len(failed_tests),
        "scores": {
            "keyword_accuracy": avg_keyword_score if successful_tests else 0,
            "response_quality": avg_quality_score if successful_tests else 0,
            "weighted_overall": avg_weighted_score if successful_tests else 0
        } if successful_tests else {},
        "grade": grade if successful_tests else "F",
        "percentage": overall_percentage if successful_tests else 0
    }

if __name__ == "__main__":
    try:
        # Check system health first
        print("🔍 Checking system health...")
        health_response = requests.get(f"{API_URL}/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            if health_data.get("initialized"):
                print("✅ System is healthy and initialized")
            else:
                print("⚠️ System is not fully initialized")
        else:
            print(f"⚠️ Health check returned: {health_response.status_code}")
        
        # Run the comprehensive test
        results = run_comprehensive_test()
        
        # Save results to file
        with open("test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n📁 Results saved to test_results.json")
        
        # Exit with appropriate code
        exit(0 if results.get("percentage", 0) >= 70 else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
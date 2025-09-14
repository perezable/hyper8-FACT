#!/usr/bin/env python3
"""
Test FACT System in degraded state - Document actual responses
"""

import requests
import json
import time
from datetime import datetime

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

# Representative test questions (5 from each persona)
TEST_QUESTIONS = {
    "price_conscious": [
        "What's the cheapest state to get a contractor license?",
        "How much does a Florida contractor license cost?",
        "Are there payment plans available?",
        "What financing options does CLP offer?",
        "What's the ROI on getting licensed?"
    ],
    "overwhelmed_veteran": [
        "I don't know where to start - can you help?",
        "What documents do I need?",
        "Can you walk me through the process step by step?",
        "What if I fail the exam?",
        "Is there a checklist I can follow?"
    ],
    "skeptical_researcher": [
        "What's your success rate?",
        "How many contractors have you helped?",
        "What states accept NASCLA?",
        "What are the exact requirements for California?",
        "What's the penalty for unlicensed work?"
    ],
    "time_pressed": [
        "What's the fastest way to get licensed?",
        "Can I expedite the process?",
        "Which state is quickest?",
        "How fast with reciprocity?",
        "What about emergency licensing?"
    ],
    "ambitious_entrepreneur": [
        "How do I get licensed in multiple states?",
        "What's the best license for growth?",
        "Can I qualify other companies?",
        "How do I maximize income?",
        "What about government contracts?"
    ]
}

def test_query(question, persona):
    """Test a single query and document the response"""
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{RAILWAY_URL}/query",
            json={
                "query": question,
                "context": "Contractor licensing inquiry"
            },
            timeout=10
        )
        
        latency = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            return {
                "persona": persona,
                "question": question,
                "response": data,
                "status_code": response.status_code,
                "latency_ms": latency,
                "has_answer": bool(data.get("answer") or data.get("response")),
                "response_text": data.get("answer") or data.get("response", "")
            }
        else:
            return {
                "persona": persona,
                "question": question,
                "error": f"HTTP {response.status_code}",
                "status_code": response.status_code,
                "latency_ms": latency,
                "has_answer": False,
                "response_text": ""
            }
    except Exception as e:
        return {
            "persona": persona,
            "question": question,
            "error": str(e),
            "status_code": 0,
            "latency_ms": (time.time() - start_time) * 1000,
            "has_answer": False,
            "response_text": ""
        }

def main():
    print("\n" + "="*70)
    print("📊 DEGRADED SYSTEM TEST - DOCUMENTING ACTUAL RESPONSES")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL: {RAILWAY_URL}")
    print(f"Knowledge Base: 1,347 entries (per /health endpoint)")
    print()
    
    # Check system health first
    print("📡 Checking system health...")
    try:
        health_response = requests.get(f"{RAILWAY_URL}/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"  Status: {health_data.get('status', 'unknown')}")
            print(f"  Enhanced Retriever Entries: {health_data.get('metrics', {}).get('enhanced_retriever_entries', 'N/A')}")
            print(f"  Circuit Breaker State: {health_data.get('metrics', {}).get('circuit_breaker_state', 'N/A')}")
            print(f"  Error Rate: {health_data.get('metrics', {}).get('error_rate', 'N/A')}%")
    except Exception as e:
        print(f"  Error checking health: {e}")
    
    print("\n" + "-"*70)
    print("TESTING QUERIES")
    print("-"*70)
    
    all_results = []
    
    for persona, questions in TEST_QUESTIONS.items():
        print(f"\n👤 {persona.replace('_', ' ').title()}")
        print("-"*40)
        
        for i, question in enumerate(questions, 1):
            result = test_query(question, persona)
            all_results.append(result)
            
            print(f"\n{i}. Question: {question}")
            print(f"   Status: HTTP {result['status_code']}")
            print(f"   Latency: {result['latency_ms']:.0f}ms")
            
            if result.get('error'):
                print(f"   Error: {result['error']}")
            
            if result.get('response'):
                print(f"   Full Response: {json.dumps(result['response'], indent=6)}")
            
            if result['response_text']:
                print(f"   Answer Text: {result['response_text'][:200]}...")
            else:
                print(f"   Answer Text: [EMPTY/NO RESPONSE]")
    
    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    
    total = len(all_results)
    successful = sum(1 for r in all_results if r['status_code'] == 200)
    with_answers = sum(1 for r in all_results if r['has_answer'])
    avg_latency = sum(r['latency_ms'] for r in all_results) / total if total > 0 else 0
    
    print(f"Total Questions: {total}")
    print(f"Successful HTTP Responses: {successful}/{total} ({successful/total*100:.1f}%)")
    print(f"Responses with Answers: {with_answers}/{total} ({with_answers/total*100:.1f}%)")
    print(f"Average Latency: {avg_latency:.0f}ms")
    
    # Analyze response patterns
    print("\n📝 Response Patterns:")
    response_types = {}
    for r in all_results:
        response_text = r['response_text']
        if not response_text:
            pattern = "EMPTY"
        elif "experiencing issues" in response_text.lower():
            pattern = "DEGRADED_MESSAGE"
        elif len(response_text) > 100:
            pattern = "FULL_ANSWER"
        else:
            pattern = "SHORT_ANSWER"
        
        response_types[pattern] = response_types.get(pattern, 0) + 1
    
    for pattern, count in response_types.items():
        print(f"  {pattern}: {count} ({count/total*100:.1f}%)")
    
    # Save detailed results
    output_file = f"degraded_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "metadata": {
                "test_date": datetime.now().isoformat(),
                "railway_url": RAILWAY_URL,
                "knowledge_base_entries": 1347,
                "system_status": "degraded"
            },
            "summary": {
                "total_questions": total,
                "successful_http": successful,
                "with_answers": with_answers,
                "avg_latency_ms": avg_latency,
                "response_patterns": response_types
            },
            "results": all_results
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    print("\n⚠️  DIAGNOSIS:")
    print("-"*40)
    if with_answers == 0:
        print("❌ The system is NOT returning any meaningful answers")
        print("   Even though 1,347 entries are loaded in memory")
        print("   The query endpoint appears to be disconnected from the knowledge base")
    elif with_answers < total / 2:
        print("⚠️  The system is returning answers for less than 50% of queries")
        print("   This indicates partial functionality issues")
    else:
        print("✅ The system is returning answers for most queries")
    
    print("\n🔧 RECOMMENDED ACTION:")
    print("   The database connection needs to be configured correctly")
    print("   The system should use the Railway PostgreSQL internal URL")
    print("   when deployed on Railway to access the knowledge base")

if __name__ == "__main__":
    main()
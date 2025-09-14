#!/usr/bin/env python3
"""
Rate-limited test to avoid Anthropic API 429 errors
Tests with delays between queries to respect rate limits
"""

import requests
import json
import time
from datetime import datetime

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

# Test questions (10 total - 2 per persona)
TEST_QUESTIONS = {
    "price_conscious": [
        "What payment plans are available for the $4,995 fee?",
        "How much does a Florida contractor license cost?"
    ],
    "overwhelmed_veteran": [
        "I don't know where to start - can you help?",
        "What documents do I need for contractor licensing?"
    ],
    "skeptical_researcher": [
        "What's your success rate with contractor licensing?",
        "What states accept NASCLA certification?"
    ],
    "time_pressed": [
        "What's the fastest way to get a contractor license?",
        "Can I expedite the licensing process?"
    ],
    "ambitious_entrepreneur": [
        "How do I get licensed in multiple states?",
        "What's the best license for business growth?"
    ]
}

def test_query(question, persona):
    """Test a single query"""
    try:
        print(f"  Sending query...", end="", flush=True)
        start_time = time.time()
        
        response = requests.post(
            f"{RAILWAY_URL}/query",
            json={
                "query": question,
                "context": "Contractor licensing inquiry"
            },
            timeout=60  # 60 second timeout
        )
        
        latency = (time.time() - start_time) * 1000
        print(f" ({latency:.0f}ms)")
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("response", data.get("answer", ""))
            
            # Score based on answer quality
            score = 0
            if answer and len(answer) > 50:
                score = 50  # Has substance
                if "apologize" not in answer.lower() and "unable" not in answer.lower():
                    score = 80  # Good answer
                    if "$" in answer or any(word in answer.lower() for word in ["clp", "contractor", "license", "state"]):
                        score = 100  # Excellent answer
            
            return {
                "success": True,
                "persona": persona,
                "question": question,
                "answer": answer,
                "score": score,
                "latency_ms": latency,
                "query_id": data.get("query_id", "")
            }
        else:
            return {
                "success": False,
                "persona": persona,
                "question": question,
                "error": f"HTTP {response.status_code}",
                "score": 0,
                "latency_ms": latency
            }
    except Exception as e:
        return {
            "success": False,
            "persona": persona,
            "question": question,
            "error": str(e),
            "score": 0,
            "latency_ms": 0
        }

def main():
    print("\n" + "="*70)
    print("🚀 RATE-LIMITED PERFORMANCE TEST")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL: {RAILWAY_URL}")
    print(f"Knowledge Base: 1,347 entries")
    print(f"Testing: 10 questions with 30-second delays to avoid rate limits")
    print()
    
    # Check health first
    print("📡 Checking system health...")
    try:
        health = requests.get(f"{RAILWAY_URL}/health", timeout=5).json()
        print(f"  Status: {health.get('status', 'unknown')}")
        print(f"  Enhanced Retriever: {health.get('metrics', {}).get('enhanced_retriever_entries', 'N/A')} entries")
        print(f"  Error Rate: {health.get('metrics', {}).get('error_rate', 'N/A'):.1f}%")
    except Exception as e:
        print(f"  Health check failed: {e}")
    
    print("\n" + "-"*70)
    
    all_results = []
    persona_scores = {}
    
    question_num = 0
    total_questions = sum(len(q) for q in TEST_QUESTIONS.values())
    
    for persona, questions in TEST_QUESTIONS.items():
        print(f"\n👤 Testing {persona.replace('_', ' ').title()}")
        persona_results = []
        
        for question in questions:
            question_num += 1
            print(f"\n[{question_num}/{total_questions}] {question[:60]}...")
            
            # Test the query
            result = test_query(question, persona)
            persona_results.append(result)
            all_results.append(result)
            
            # Display result
            if result["success"]:
                print(f"  ✅ Score: {result['score']}/100")
                if result["answer"]:
                    preview = result["answer"][:150].replace('\n', ' ')
                    if "apologize" in preview.lower() or "unable" in preview.lower():
                        print(f"  ⚠️  Generic response: {preview}...")
                    else:
                        print(f"  📝 Answer: {preview}...")
            else:
                print(f"  ❌ Error: {result['error']}")
            
            # Wait 30 seconds between queries to avoid rate limits
            if question_num < total_questions:
                print(f"  ⏳ Waiting 30 seconds before next query to avoid rate limits...")
                time.sleep(30)
        
        # Calculate persona average
        scores = [r["score"] for r in persona_results]
        avg_score = sum(scores) / len(scores) if scores else 0
        persona_scores[persona] = avg_score
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    successful = sum(1 for r in all_results if r["success"])
    all_scores = [r["score"] for r in all_results]
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
    avg_latency = sum(r["latency_ms"] for r in all_results if r["success"]) / successful if successful > 0 else 0
    
    print(f"Total Questions: {len(all_results)}")
    print(f"Successful: {successful}/{len(all_results)} ({successful/len(all_results)*100:.1f}%)")
    print(f"Average Score: {avg_score:.1f}/100")
    print(f"Average Latency: {avg_latency:.0f}ms")
    
    # Grade
    if avg_score >= 80:
        grade = "B"
    elif avg_score >= 60:
        grade = "C"
    elif avg_score >= 40:
        grade = "D"
    else:
        grade = "F"
    
    print(f"Grade: {grade}")
    
    print("\n📊 Persona Scores:")
    for persona, score in persona_scores.items():
        print(f"  {persona.replace('_', ' ').title()}: {score:.1f}/100")
    
    # Analysis
    print("\n📈 Analysis:")
    generic_responses = sum(1 for r in all_results if r.get("answer") and ("apologize" in r["answer"].lower() or "unable" in r["answer"].lower()))
    good_responses = sum(1 for r in all_results if r["score"] >= 80)
    
    print(f"  Generic/Failed Responses: {generic_responses}/{len(all_results)} ({generic_responses/len(all_results)*100:.1f}%)")
    print(f"  Good Responses: {good_responses}/{len(all_results)} ({good_responses/len(all_results)*100:.1f}%)")
    
    if generic_responses > len(all_results) / 2:
        print("\n⚠️  ISSUE DETECTED:")
        print("  The system is returning generic apology messages")
        print("  This indicates the Anthropic API is being rate-limited")
        print("  or unable to generate responses from the knowledge base")
    
    # Save results
    output_file = f"rate_limited_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "metadata": {
                "test_date": datetime.now().isoformat(),
                "knowledge_base_entries": 1347,
                "delay_between_queries": 30
            },
            "summary": {
                "avg_score": avg_score,
                "success_rate": successful/len(all_results)*100 if all_results else 0,
                "avg_latency_ms": avg_latency,
                "grade": grade
            },
            "persona_scores": persona_scores,
            "results": all_results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")

if __name__ == "__main__":
    main()
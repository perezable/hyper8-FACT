#!/usr/bin/env python3
"""
Throttled Comprehensive Test for FACT System
Tests with delays to avoid Anthropic API rate limits
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"
DELAY_BETWEEN_QUERIES = 15  # 15 seconds between queries to avoid rate limits

# Comprehensive test questions (40 total - 8 per persona)
TEST_QUESTIONS = {
    "price_conscious": [
        "What payment plans are available for the $4,995 fee?",
        "How much does a Florida contractor license cost total?",
        "What's the cheapest state to get a contractor license?",
        "Are there financing options available?",
        "What's included in the $1,400 CLP fee?",
        "Can I get a discount for multiple state licenses?",
        "How much is the California contractor bond?",
        "What's the ROI on getting licensed?"
    ],
    "overwhelmed_veteran": [
        "I don't know where to start - can you help?",
        "What documents do I need for contractor licensing?",
        "Can you walk me through the process step by step?",
        "What if I fail the exam?",
        "Is there a checklist I can follow?",
        "How do I know which license I need?",
        "Can someone help me with paperwork?",
        "What support is available for veterans?"
    ],
    "skeptical_researcher": [
        "What's your success rate with contractors?",
        "How many contractors have you helped?",
        "What states accept NASCLA certification?",
        "What are the exact requirements for California?",
        "What's your BBB rating?",
        "Can I see testimonials?",
        "What's the penalty for unlicensed work?",
        "How do you compare to competitors?"
    ],
    "time_pressed": [
        "What's the fastest way to get licensed?",
        "Can I expedite the process?",
        "Which state is quickest to get licensed?",
        "How fast can I get licensed with reciprocity?",
        "What about emergency licensing?",
        "Can I work before license arrives?",
        "What's priority processing time?",
        "How quick is online exam?"
    ],
    "ambitious_entrepreneur": [
        "How do I get licensed in multiple states?",
        "What's the best license for growth?",
        "Can I qualify other companies?",
        "How do I maximize income as a contractor?",
        "What about government contracts?",
        "How to become a general contractor?",
        "Best states for contractors?",
        "What licenses command highest fees?"
    ]
}

def test_query(question: str, persona: str) -> Dict:
    """Test a single query with the FACT system"""
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{RAILWAY_URL}/query",
            json={
                "query": question,
                "context": "Contractor licensing inquiry"
            },
            timeout=30
        )
        
        latency = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("response", data.get("answer", ""))
            
            # Score the response
            score = score_response(question, answer, persona)
            
            return {
                "success": True,
                "persona": persona,
                "question": question,
                "answer": answer,
                "score": score,
                "latency_ms": latency,
                "query_id": data.get("query_id", ""),
                "timestamp": data.get("timestamp", "")
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
            "latency_ms": (time.time() - start_time) * 1000
        }

def score_response(question: str, answer: str, persona: str) -> int:
    """Score a response based on quality criteria"""
    if not answer:
        return 0
    
    score = 0
    
    # Check for error messages
    if "apologize" in answer.lower() or "unable to generate" in answer.lower():
        return 0
    
    if "experiencing issues" in answer.lower():
        return 0
    
    # Base scoring
    if len(answer) > 50:
        score += 30  # Has substance
    if len(answer) > 200:
        score += 20  # Detailed response
    
    # Check for relevant content
    persona_keywords = {
        "price_conscious": ["cost", "price", "$", "fee", "payment", "financing", "discount"],
        "overwhelmed_veteran": ["help", "support", "step", "guide", "assist", "veteran"],
        "skeptical_researcher": ["data", "rate", "%", "proven", "requirements", "state"],
        "time_pressed": ["fast", "quick", "immediate", "day", "hour", "expedite"],
        "ambitious_entrepreneur": ["growth", "expand", "multiple", "income", "scale", "profit"]
    }
    
    keywords_found = sum(1 for kw in persona_keywords.get(persona, []) 
                        if kw.lower() in answer.lower())
    score += min(keywords_found * 10, 30)
    
    # Check for specific data
    if any(char.isdigit() for char in answer):
        score += 10  # Contains numbers
    
    # Check for CLP specific info
    if "clp" in answer.lower() or "contractor licensing pros" in answer.lower():
        score += 10
    
    return min(100, score)

def main():
    print("\n" + "="*70)
    print("🚀 THROTTLED COMPREHENSIVE TEST - FACT SYSTEM")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL: {RAILWAY_URL}")
    print(f"Knowledge Base: 1,347 entries")
    print(f"Delay between queries: {DELAY_BETWEEN_QUERIES} seconds")
    print(f"Total questions: 40 (8 per persona)")
    print()
    
    # Check system health
    print("📡 Checking system health...")
    try:
        health = requests.get(f"{RAILWAY_URL}/health", timeout=5).json()
        print(f"  Status: {health.get('status', 'unknown')}")
        print(f"  Enhanced Retriever: {health.get('metrics', {}).get('enhanced_retriever_entries', 'N/A')} entries")
        print(f"  Error Rate: {health.get('metrics', {}).get('error_rate', 'N/A'):.1f}%")
        print(f"  Total Queries: {health.get('metrics', {}).get('total_queries', 0)}")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n" + "-"*70)
    print("STARTING THROTTLED TEST")
    print("-"*70)
    
    all_results = []
    persona_scores = {}
    total_questions = sum(len(q) for q in TEST_QUESTIONS.values())
    question_num = 0
    
    for persona, questions in TEST_QUESTIONS.items():
        print(f"\n👤 Testing {persona.replace('_', ' ').title()} Persona")
        print("-"*40)
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
                if result["score"] > 0:
                    print(f"  ✅ Score: {result['score']}/100 | Latency: {result['latency_ms']:.0f}ms")
                    preview = result["answer"][:150].replace('\n', ' ')
                    print(f"  📝 {preview}...")
                else:
                    print(f"  ❌ Score: 0/100 (Generic/Error response)")
                    print(f"  Response: {result['answer'][:100]}...")
            else:
                print(f"  ❌ Error: {result['error']}")
            
            # Delay between queries
            if question_num < total_questions:
                print(f"  ⏳ Waiting {DELAY_BETWEEN_QUERIES}s before next query...")
                time.sleep(DELAY_BETWEEN_QUERIES)
        
        # Calculate persona average
        scores = [r["score"] for r in persona_results]
        avg_score = sum(scores) / len(scores) if scores else 0
        persona_scores[persona] = avg_score
        print(f"\n  Persona Average: {avg_score:.1f}/100")
    
    # Generate summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    successful = sum(1 for r in all_results if r["success"])
    good_responses = sum(1 for r in all_results if r["score"] > 50)
    all_scores = [r["score"] for r in all_results]
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
    
    print(f"Total Questions: {len(all_results)}")
    print(f"Successful Queries: {successful}/{len(all_results)} ({successful/len(all_results)*100:.1f}%)")
    print(f"Good Responses (>50): {good_responses}/{len(all_results)} ({good_responses/len(all_results)*100:.1f}%)")
    print(f"Average Score: {avg_score:.1f}/100")
    
    # Grade
    if avg_score >= 80:
        grade = "B"
    elif avg_score >= 60:
        grade = "C"
    elif avg_score >= 40:
        grade = "D"
    else:
        grade = "F"
    
    print(f"Overall Grade: {grade}")
    
    print("\n📊 Persona Breakdown:")
    for persona, score in persona_scores.items():
        print(f"  {persona.replace('_', ' ').title()}: {score:.1f}/100")
    
    # Best and worst
    sorted_results = sorted(all_results, key=lambda x: x["score"], reverse=True)
    
    print("\n✅ Top 3 Performing Questions:")
    for r in sorted_results[:3]:
        if r["score"] > 0:
            print(f"  [{r['score']}/100] {r['question'][:60]}...")
    
    print("\n❌ Bottom 3 Performing Questions:")
    for r in sorted_results[-3:]:
        print(f"  [{r['score']}/100] {r['question'][:60]}...")
        if r.get("error"):
            print(f"    Error: {r['error']}")
    
    # Error analysis
    error_types = {}
    for r in all_results:
        if r["score"] == 0:
            answer = r.get("answer", "")
            if "apologize" in answer.lower():
                error_types["API_GENERATION_ERROR"] = error_types.get("API_GENERATION_ERROR", 0) + 1
            elif "experiencing issues" in answer.lower():
                error_types["SYSTEM_DEGRADED"] = error_types.get("SYSTEM_DEGRADED", 0) + 1
            elif not answer:
                error_types["EMPTY_RESPONSE"] = error_types.get("EMPTY_RESPONSE", 0) + 1
            else:
                error_types["OTHER"] = error_types.get("OTHER", 0) + 1
    
    if error_types:
        print("\n⚠️ Error Types:")
        for error_type, count in error_types.items():
            print(f"  {error_type}: {count}")
    
    # Save results
    output_file = f"throttled_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "metadata": {
                "test_date": datetime.now().isoformat(),
                "knowledge_base_entries": 1347,
                "delay_seconds": DELAY_BETWEEN_QUERIES,
                "total_questions": len(all_results)
            },
            "summary": {
                "avg_score": avg_score,
                "success_rate": successful/len(all_results)*100 if all_results else 0,
                "good_response_rate": good_responses/len(all_results)*100 if all_results else 0,
                "grade": grade
            },
            "persona_scores": persona_scores,
            "results": all_results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Comparison with baseline
    print("\n📈 Performance Comparison:")
    print("  Baseline (before issues): 67.7/100")
    print(f"  Current: {avg_score:.1f}/100")
    improvement = avg_score - 67.7
    print(f"  Change: {'+' if improvement >= 0 else ''}{improvement:.1f} points")
    
    # Total test time
    test_duration = len(all_results) * DELAY_BETWEEN_QUERIES
    print(f"\n⏱️ Total test duration: ~{test_duration/60:.1f} minutes")

if __name__ == "__main__":
    main()
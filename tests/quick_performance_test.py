#!/usr/bin/env python3
"""
Quick Performance Test for FACT System
Tests sample questions from each persona
"""

import requests
import json
import time
from datetime import datetime

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

# Sample test questions (5 per persona = 25 total)
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

def test_query(question):
    """Test a single query"""
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
                "question": question,
                "answer": data.get("answer", ""),
                "latency": latency,
                "status": "success",
                "score": score_response(question, data.get("answer", ""))
            }
        else:
            return {
                "question": question,
                "error": f"HTTP {response.status_code}",
                "latency": latency,
                "status": "error",
                "score": 0
            }
    except Exception as e:
        return {
            "question": question,
            "error": str(e),
            "latency": 0,
            "status": "error",
            "score": 0
        }

def score_response(question, answer):
    """Simple scoring based on answer quality"""
    if not answer:
        return 0
    
    score = 0
    
    # Length check
    if len(answer) > 50:
        score += 30
    if len(answer) > 200:
        score += 20
    
    # Contains specifics
    if any(char.isdigit() for char in answer):
        score += 20  # Has numbers
    
    if "$" in answer or "cost" in answer.lower() or "fee" in answer.lower():
        score += 10  # Financial info
    
    if "step" in answer.lower() or "process" in answer.lower():
        score += 10  # Process info
    
    if "clp" in answer.lower() or "954-904-1064" in answer:
        score += 10  # CLP specific
    
    return min(100, score)

def main():
    print("\n" + "="*70)
    print("⚡ QUICK PERFORMANCE TEST - ENHANCED KNOWLEDGE BASE")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Knowledge Base: 1,347 entries")
    print(f"Testing: 25 sample questions (5 per persona)")
    print()
    
    all_results = []
    persona_scores = {}
    
    # Test each persona
    for persona, questions in TEST_QUESTIONS.items():
        print(f"Testing {persona.replace('_', ' ').title()}...")
        persona_results = []
        
        for question in questions:
            result = test_query(question)
            result["persona"] = persona
            persona_results.append(result)
            all_results.append(result)
            
            # Show inline result
            status_icon = "✅" if result["status"] == "success" else "❌"
            score = result.get("score", 0)
            print(f"  {status_icon} [{score:3d}/100] {question[:50]}...")
            
            # Show answer preview if successful
            if result["status"] == "success" and result.get("answer"):
                preview = result["answer"][:100].replace('\n', ' ')
                print(f"      → {preview}...")
        
        # Calculate persona average
        scores = [r["score"] for r in persona_results]
        avg_score = sum(scores) / len(scores) if scores else 0
        persona_scores[persona] = avg_score
        print(f"  Persona Average: {avg_score:.1f}/100\n")
    
    # Overall summary
    print("="*70)
    print("📊 SUMMARY")
    print("="*70)
    
    total_questions = len(all_results)
    successful = sum(1 for r in all_results if r["status"] == "success")
    all_scores = [r["score"] for r in all_results]
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
    
    print(f"Total Questions: {total_questions}")
    print(f"Successful: {successful}/{total_questions} ({successful/total_questions*100:.1f}%)")
    print(f"Average Score: {avg_score:.1f}/100")
    
    # Grade
    if avg_score >= 90:
        grade = "A"
    elif avg_score >= 80:
        grade = "B"
    elif avg_score >= 70:
        grade = "C"
    elif avg_score >= 60:
        grade = "D"
    else:
        grade = "F"
    
    print(f"Grade: {grade}")
    
    print("\n📊 Persona Scores:")
    for persona, score in persona_scores.items():
        print(f"  {persona.replace('_', ' ').title()}: {score:.1f}/100")
    
    # Best and worst
    sorted_results = sorted(all_results, key=lambda x: x["score"], reverse=True)
    
    print("\n✅ Best Performing:")
    for r in sorted_results[:3]:
        print(f"  [{r['score']}/100] {r['question'][:60]}...")
    
    print("\n❌ Worst Performing:")
    for r in sorted_results[-3:]:
        print(f"  [{r['score']}/100] {r['question'][:60]}...")
        if r.get("error"):
            print(f"    Error: {r['error']}")
    
    # Save results
    output_file = f"quick_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "metadata": {
                "test_date": datetime.now().isoformat(),
                "knowledge_base_entries": 1347,
                "total_questions": total_questions
            },
            "summary": {
                "avg_score": avg_score,
                "success_rate": successful/total_questions*100,
                "grade": grade
            },
            "persona_scores": persona_scores,
            "results": all_results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Comparison
    print("\n📈 Comparison with Previous Test:")
    print("  Previous (1,055 entries): 67.7/100")
    print(f"  Current (1,347 entries): {avg_score:.1f}/100")
    improvement = avg_score - 67.7
    print(f"  Change: {'+' if improvement >= 0 else ''}{improvement:.1f} points")

if __name__ == "__main__":
    main()
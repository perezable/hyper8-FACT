#!/usr/bin/env python3
"""
Test FACT system on Railway with 200 synthetic questions
"""

import json
import requests
import time
from datetime import datetime
import statistics

# Railway endpoint
WEBHOOK_URL = "https://hyper8-fact-fact-system.up.railway.app/vapi-debug/webhook"

# Load synthetic questions
def load_questions():
    """Load the 200 synthetic questions"""
    try:
        with open('tests/synthetic_questions.json', 'r') as f:
            return json.load(f)
    except:
        # Generate sample questions if file doesn't exist
        return generate_sample_questions()

def generate_sample_questions():
    """Generate sample questions for each persona"""
    personas = {
        "price_conscious": [
            "How much does a Georgia contractor license cost?",
            "What's the cheapest state to get licensed in?",
            "Are there payment plans available?",
            "Is it worth the $4,995 investment?",
            "What's the ROI on your program?"
        ],
        "overwhelmed_veteran": [
            "I don't know where to start with licensing",
            "How long does the whole process take?",
            "Is the test hard to pass?",
            "Can you help me step by step?",
            "What documents do I need?"
        ],
        "skeptical_researcher": [
            "What's your actual success rate?",
            "Can you prove the 98% approval claim?",
            "How do you compare to competitors?",
            "Show me real customer results",
            "What data backs up your claims?"
        ],
        "time_pressed": [
            "What's the fastest way to get licensed?",
            "Can I expedite the process?",
            "How quickly can I start bidding?",
            "Do you offer rush processing?",
            "What's the absolute minimum timeline?"
        ],
        "ambitious_entrepreneur": [
            "How do I expand to multiple states?",
            "Tell me about the qualifier network income",
            "Which states have the best opportunities?",
            "How can I scale my contracting business?",
            "What's the passive income potential?"
        ]
    }
    
    questions = []
    for persona, persona_questions in personas.items():
        for q in persona_questions:
            questions.append({
                "id": f"{persona}_{len(questions)+1}",
                "question": q,
                "persona": persona,
                "category": "general"
            })
    
    return questions

def query_fact_system(question_text):
    """Query the FACT system via webhook"""
    payload = {
        "message": {
            "type": "tool-calls",
            "toolCalls": [
                {
                    "id": f"test-{int(time.time()*1000)}",
                    "type": "function",
                    "function": {
                        "name": "searchKnowledge",
                        "arguments": {
                            "query": question_text
                        }
                    }
                }
            ]
        }
    }
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "response": result,
                "time_ms": response.elapsed.total_seconds() * 1000
            }
        else:
            return {
                "success": False,
                "error": f"Status {response.status_code}",
                "time_ms": response.elapsed.total_seconds() * 1000
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "time_ms": 0
        }

def score_response(question, response):
    """Score the response quality"""
    if not response["success"]:
        return 0
    
    # Basic scoring based on response presence and length
    try:
        result_text = json.dumps(response["response"])
        
        # Score components
        has_answer = 1 if "answer" in result_text or "result" in result_text else 0
        has_content = 1 if len(result_text) > 100 else 0
        response_time_score = 1 if response["time_ms"] < 1000 else 0.5 if response["time_ms"] < 3000 else 0
        
        # Check for persona-specific elements
        persona_score = 0
        if question["persona"] == "price_conscious" and "$" in result_text:
            persona_score = 1
        elif question["persona"] == "skeptical_researcher" and ("%" in result_text or "data" in result_text):
            persona_score = 1
        elif question["persona"] == "time_pressed" and any(word in result_text.lower() for word in ["fast", "quick", "expedite"]):
            persona_score = 1
        elif question["persona"] == "ambitious_entrepreneur" and any(word in result_text.lower() for word in ["expand", "scale", "growth"]):
            persona_score = 1
        elif question["persona"] == "overwhelmed_veteran" and any(word in result_text.lower() for word in ["step", "help", "guide"]):
            persona_score = 1
        
        # Calculate total score (0-100)
        total_score = (has_answer * 30 + has_content * 30 + response_time_score * 20 + persona_score * 20)
        
        return total_score
    except:
        return 0

def main():
    print("\n🚀 FACT System Railway Test Suite")
    print("=" * 60)
    print(f"Testing endpoint: {WEBHOOK_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Load questions
    questions = load_questions()[:50]  # Test first 50 questions
    print(f"\n📝 Testing {len(questions)} questions across 5 personas")
    
    # Test each question
    results = []
    persona_scores = {}
    response_times = []
    
    print("\n🔍 Running tests...")
    for i, question in enumerate(questions):
        print(f"\r  Progress: {i+1}/{len(questions)}", end="")
        
        # Query FACT system
        response = query_fact_system(question["question"])
        
        # Score response
        score = score_response(question, response)
        
        # Track results
        results.append({
            "question": question,
            "response": response,
            "score": score
        })
        
        # Track by persona
        persona = question["persona"]
        if persona not in persona_scores:
            persona_scores[persona] = []
        persona_scores[persona].append(score)
        
        # Track response time
        if response["success"]:
            response_times.append(response["time_ms"])
        
        # Small delay to avoid rate limiting
        time.sleep(0.1)
    
    print("\n\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    # Calculate overall metrics
    all_scores = [r["score"] for r in results]
    successful = len([r for r in results if r["response"]["success"]])
    
    print(f"\n✅ Success Rate: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
    print(f"📈 Average Score: {statistics.mean(all_scores):.1f}/100")
    print(f"📉 Min Score: {min(all_scores):.1f}/100")
    print(f"📊 Max Score: {max(all_scores):.1f}/100")
    
    if response_times:
        print(f"\n⏱️  Response Times:")
        print(f"   Average: {statistics.mean(response_times):.0f}ms")
        print(f"   Median: {statistics.median(response_times):.0f}ms")
        print(f"   95th percentile: {sorted(response_times)[int(len(response_times)*0.95)]:.0f}ms")
    
    # Persona breakdown
    print(f"\n👥 Performance by Persona:")
    for persona, scores in persona_scores.items():
        avg_score = statistics.mean(scores) if scores else 0
        grade = "A" if avg_score >= 90 else "B" if avg_score >= 80 else "C" if avg_score >= 70 else "D" if avg_score >= 60 else "F"
        print(f"   {persona.replace('_', ' ').title()}: {avg_score:.1f}/100 (Grade: {grade})")
    
    # Grade distribution
    grade_counts = {
        "A (90-100)": len([s for s in all_scores if s >= 90]),
        "B (80-89)": len([s for s in all_scores if 80 <= s < 90]),
        "C (70-79)": len([s for s in all_scores if 70 <= s < 80]),
        "D (60-69)": len([s for s in all_scores if 60 <= s < 70]),
        "F (0-59)": len([s for s in all_scores if s < 60])
    }
    
    print(f"\n📊 Grade Distribution:")
    for grade, count in grade_counts.items():
        bar = "█" * int(count/len(results)*50)
        print(f"   {grade}: {bar} {count} ({count/len(results)*100:.1f}%)")
    
    # Identify weak areas
    print(f"\n⚠️  Weakest Performing Questions:")
    sorted_results = sorted(results, key=lambda x: x["score"])[:5]
    for i, result in enumerate(sorted_results, 1):
        print(f"   {i}. {result['question']['question'][:60]}...")
        print(f"      Score: {result['score']}/100, Persona: {result['question']['persona']}")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"fact_test_results_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "summary": {
                "total_tests": len(results),
                "success_rate": successful/len(results),
                "average_score": statistics.mean(all_scores),
                "average_response_time_ms": statistics.mean(response_times) if response_times else 0
            },
            "persona_scores": {k: statistics.mean(v) for k, v in persona_scores.items()},
            "grade_distribution": grade_counts,
            "detailed_results": results[:10]  # Save first 10 for review
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    # Final recommendations
    print("\n" + "=" * 60)
    print("🎯 Recommendations")
    print("=" * 60)
    
    avg_score = statistics.mean(all_scores)
    if avg_score >= 80:
        print("✅ System performing well! Focus on optimizing response times.")
    elif avg_score >= 70:
        print("🟡 Good performance with room for improvement in content quality.")
    elif avg_score >= 60:
        print("🟠 Moderate performance. Consider expanding knowledge base.")
    else:
        print("🔴 Significant improvements needed in response quality and coverage.")
    
    # Persona-specific recommendations
    print("\n📋 Persona-Specific Improvements:")
    for persona, scores in persona_scores.items():
        avg = statistics.mean(scores) if scores else 0
        if avg < 70:
            if persona == "price_conscious":
                print(f"   • {persona}: Add more pricing and ROI information")
            elif persona == "skeptical_researcher":
                print(f"   • {persona}: Include more data, statistics, and proof points")
            elif persona == "time_pressed":
                print(f"   • {persona}: Emphasize speed and efficiency in responses")
            elif persona == "ambitious_entrepreneur":
                print(f"   • {persona}: Add growth and scaling strategies")
            elif persona == "overwhelmed_veteran":
                print(f"   • {persona}: Simplify responses with step-by-step guidance")

if __name__ == "__main__":
    main()
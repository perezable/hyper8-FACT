#!/usr/bin/env python3
"""
Run full test of 200 synthetic questions against FACT system
Document every question, answer, score, and latency
"""

import json
import requests
import time
from datetime import datetime
import statistics
import sys

# Railway endpoint
WEBHOOK_URL = "https://hyper8-fact-fact-system.up.railway.app/vapi-debug/webhook"

def generate_200_questions():
    """Generate all 200 synthetic questions"""
    questions = []
    
    # Price-Conscious Penny (40 questions)
    price_conscious = [
        "How much does a Georgia contractor license cost all-in?",
        "What's the cheapest state to get licensed in?",
        "Are there payment plans available for the $4,995 fee?",
        "Is the investment worth it compared to DIY?",
        "What's the ROI on your licensing program?",
        "Can I get a discount if I refer others?",
        "How much can I save doing it myself?",
        "What hidden fees should I expect?",
        "Do you offer any guarantees on the investment?",
        "What's included in the $4,995 price?",
        "How much does a Florida license cost?",
        "Compare your price to competitors",
        "Is there a money-back guarantee?",
        "What's the cost breakdown by state?",
        "Do prices vary by license type?",
        "Are there additional exam fees?",
        "What about renewal costs?",
        "How much for multiple state licenses?",
        "Is financing available?",
        "What's the average cost nationwide?",
        "New York contractor license cost?",
        "Illinois licensing fees breakdown",
        "Pennsylvania license total cost",
        "Ohio contractor fees all-in",
        "Michigan licensing investment",
        "North Carolina license pricing",
        "Virginia contractor costs",
        "Arizona licensing fees",
        "Colorado contractor license cost",
        "Washington state license pricing",
        "Texas contractor license fees",
        "California licensing total cost",
        "Nevada contractor license price",
        "Oregon licensing fees",
        "Utah contractor costs",
        "Tennessee license pricing",
        "Kentucky contractor fees",
        "Indiana licensing costs",
        "Missouri contractor pricing",
        "Alabama license fees total"
    ]
    
    # Overwhelmed Veteran (40 questions)
    overwhelmed = [
        "I don't even know where to start - help?",
        "How long is this whole process?",
        "Do I need to study for tests?",
        "What documents do I need?",
        "Can you walk me through step-by-step?",
        "Is this really complicated?",
        "I'm confused about the requirements",
        "How do I know which license I need?",
        "What if I fail the test?",
        "Do you provide study materials?",
        "Is there someone to help me?",
        "How many forms are there?",
        "What's the first step I should take?",
        "Can you simplify this for me?",
        "I'm overwhelmed by all the options",
        "Do I need a lawyer?",
        "What about insurance requirements?",
        "How do I prove my experience?",
        "What if I have a criminal record?",
        "Can you handle everything for me?",
        "Georgia requirements seem complex",
        "Florida process is confusing",
        "New York licensing overwhelming",
        "California requirements help",
        "Texas process seems difficult",
        "Illinois licensing confusion",
        "Pennsylvania requirements unclear",
        "Ohio process questions",
        "Michigan licensing help needed",
        "North Carolina confusing rules",
        "Virginia requirements assistance",
        "Arizona process overwhelming",
        "Colorado licensing complexity",
        "Washington requirements help",
        "Oregon process confusion",
        "Nevada licensing assistance",
        "Utah requirements unclear",
        "Tennessee process help",
        "Kentucky licensing confusion",
        "Indiana requirements assistance"
    ]
    
    # Skeptical Researcher (40 questions)
    skeptical = [
        "What's your actual success rate with data?",
        "Can you prove the 98% approval claim?",
        "Show me competitor comparisons",
        "What independent reviews say about you?",
        "How many clients have you helped?",
        "What's your BBB rating?",
        "Any lawsuits against your company?",
        "Show me real testimonials",
        "What certifications do you have?",
        "How long have you been in business?",
        "What's your refund rate?",
        "Prove your ROI calculations",
        "Show me case studies",
        "What failures have you had?",
        "How do you verify success?",
        "What data backs your claims?",
        "Third-party validation sources?",
        "Industry recognition or awards?",
        "Government endorsements?",
        "Statistical evidence please",
        "Georgia success rate data",
        "Florida approval statistics",
        "California success metrics",
        "Texas approval percentages",
        "New York success data",
        "Illinois approval rates",
        "Pennsylvania statistics",
        "Ohio success metrics",
        "Michigan approval data",
        "North Carolina statistics",
        "Virginia success rates",
        "Arizona approval data",
        "Colorado success metrics",
        "Washington statistics",
        "Oregon approval rates",
        "Nevada success data",
        "Utah approval metrics",
        "Tennessee statistics",
        "Kentucky success rates",
        "Indiana approval data"
    ]
    
    # Time-Pressed Pro (40 questions)
    time_pressed = [
        "What's the fastest path to licensing?",
        "Can I expedite the process?",
        "How quickly can I start bidding?",
        "Rush processing available?",
        "Minimum timeline to license?",
        "Can you fast-track my application?",
        "Emergency licensing options?",
        "How fast with your help vs alone?",
        "Same-day processing possible?",
        "Weekend or evening services?",
        "Can I start before approval?",
        "Temporary license while waiting?",
        "Priority processing cost?",
        "Fastest state to get licensed?",
        "Skip any requirements legally?",
        "Accelerated exam scheduling?",
        "How to avoid delays?",
        "Common bottlenecks to avoid?",
        "24-hour turnaround possible?",
        "Can you guarantee timeline?",
        "Georgia fast-track options",
        "Florida expedited licensing",
        "California rush processing",
        "Texas quick approval",
        "New York fast licensing",
        "Illinois expedited process",
        "Pennsylvania quick path",
        "Ohio fast-track licensing",
        "Michigan rush approval",
        "North Carolina quick process",
        "Virginia expedited licensing",
        "Arizona fast approval",
        "Colorado quick licensing",
        "Washington rush process",
        "Oregon expedited path",
        "Nevada fast licensing",
        "Utah quick approval",
        "Tennessee rush process",
        "Kentucky fast-track",
        "Indiana expedited licensing"
    ]
    
    # Ambitious Entrepreneur (40 questions)
    ambitious = [
        "How do I expand to multiple states?",
        "What about the qualifier network income?",
        "Best states for commercial contracts?",
        "How to scale my contracting business?",
        "Passive income opportunities?",
        "Can I license others under me?",
        "Multi-state licensing strategy?",
        "Government contract requirements?",
        "How to become a qualifier?",
        "Income potential with license?",
        "Best markets for growth?",
        "How to dominate my market?",
        "Licensing for business expansion?",
        "Interstate reciprocity agreements?",
        "Corporate licensing options?",
        "How to build a contractor empire?",
        "Franchise opportunities with license?",
        "International expansion possibilities?",
        "Private equity requirements?",
        "Exit strategy considerations?",
        "Georgia business opportunities",
        "Florida commercial markets",
        "California growth potential",
        "Texas expansion options",
        "New York business scaling",
        "Illinois commercial opportunities",
        "Pennsylvania growth markets",
        "Ohio business expansion",
        "Michigan commercial potential",
        "North Carolina growth options",
        "Virginia business opportunities",
        "Arizona expansion potential",
        "Colorado commercial markets",
        "Washington growth scaling",
        "Oregon business opportunities",
        "Nevada expansion options",
        "Utah commercial potential",
        "Tennessee growth markets",
        "Kentucky business scaling",
        "Indiana expansion opportunities"
    ]
    
    # Create question objects with metadata
    for i, q in enumerate(price_conscious):
        questions.append({
            "id": f"pc_{i+1}",
            "question": q,
            "persona": "price_conscious",
            "category": "cost" if "cost" in q.lower() or "price" in q.lower() or "$" in q else "general"
        })
    
    for i, q in enumerate(overwhelmed):
        questions.append({
            "id": f"ov_{i+1}",
            "question": q,
            "persona": "overwhelmed_veteran",
            "category": "process" if "process" in q.lower() or "step" in q.lower() else "requirements"
        })
    
    for i, q in enumerate(skeptical):
        questions.append({
            "id": f"sr_{i+1}",
            "question": q,
            "persona": "skeptical_researcher",
            "category": "validation" if "prove" in q.lower() or "data" in q.lower() else "statistics"
        })
    
    for i, q in enumerate(time_pressed):
        questions.append({
            "id": f"tp_{i+1}",
            "question": q,
            "persona": "time_pressed",
            "category": "timeline" if "fast" in q.lower() or "quick" in q.lower() else "expedite"
        })
    
    for i, q in enumerate(ambitious):
        questions.append({
            "id": f"ae_{i+1}",
            "question": q,
            "persona": "ambitious_entrepreneur",
            "category": "growth" if "expand" in q.lower() or "scale" in q.lower() else "opportunity"
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
        start_time = time.time()
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        latency_ms = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            return {
                "success": True,
                "response": response.json(),
                "latency_ms": latency_ms,
                "status_code": 200
            }
        else:
            return {
                "success": False,
                "response": None,
                "latency_ms": latency_ms,
                "status_code": response.status_code,
                "error": f"Status {response.status_code}"
            }
    except requests.Timeout:
        return {
            "success": False,
            "response": None,
            "latency_ms": 10000,
            "status_code": 0,
            "error": "Timeout after 10 seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "response": None,
            "latency_ms": 0,
            "status_code": 0,
            "error": str(e)
        }

def score_response(question, result):
    """Score the response quality (0-100)"""
    if not result["success"]:
        return 0
    
    score = 0
    response_text = json.dumps(result["response"]) if result["response"] else ""
    
    # Base scoring (40 points for having a response)
    if response_text and len(response_text) > 50:
        score += 40
    
    # Content quality (20 points)
    if "answer" in response_text or "result" in response_text:
        score += 10
    if "debug_info" not in response_text or len(response_text) > 200:
        score += 10
    
    # Response time scoring (20 points)
    if result["latency_ms"] < 200:
        score += 20
    elif result["latency_ms"] < 500:
        score += 15
    elif result["latency_ms"] < 1000:
        score += 10
    elif result["latency_ms"] < 2000:
        score += 5
    
    # Persona-specific scoring (20 points)
    persona = question["persona"]
    if persona == "price_conscious":
        if any(word in response_text.lower() for word in ["cost", "price", "$", "fee", "investment"]):
            score += 20
    elif persona == "overwhelmed_veteran":
        if any(word in response_text.lower() for word in ["help", "step", "guide", "simple", "easy"]):
            score += 20
    elif persona == "skeptical_researcher":
        if any(word in response_text.lower() for word in ["data", "rate", "%", "success", "proof"]):
            score += 20
    elif persona == "time_pressed":
        if any(word in response_text.lower() for word in ["fast", "quick", "expedite", "rush", "day"]):
            score += 20
    elif persona == "ambitious_entrepreneur":
        if any(word in response_text.lower() for word in ["expand", "scale", "grow", "income", "opportunity"]):
            score += 20
    
    return min(score, 100)

def main():
    print("\n" + "="*80)
    print("🚀 FACT SYSTEM COMPREHENSIVE TEST - 200 QUESTIONS")
    print("="*80)
    print(f"Endpoint: {WEBHOOK_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Generate all 200 questions
    questions = generate_200_questions()
    print(f"\n📝 Generated {len(questions)} test questions")
    
    # Initialize results storage
    all_results = []
    persona_stats = {
        "price_conscious": {"scores": [], "latencies": [], "successes": 0, "total": 0},
        "overwhelmed_veteran": {"scores": [], "latencies": [], "successes": 0, "total": 0},
        "skeptical_researcher": {"scores": [], "latencies": [], "successes": 0, "total": 0},
        "time_pressed": {"scores": [], "latencies": [], "successes": 0, "total": 0},
        "ambitious_entrepreneur": {"scores": [], "latencies": [], "successes": 0, "total": 0}
    }
    
    print("\n🔬 Testing each question...")
    print("-"*80)
    
    # Test each question
    for i, question in enumerate(questions):
        print(f"\n[{i+1}/200] Testing: {question['id']}")
        print(f"  Question: {question['question'][:60]}...")
        print(f"  Persona: {question['persona']}")
        
        # Query FACT system
        result = query_fact_system(question["question"])
        
        # Score the response
        score = score_response(question, result)
        
        # Get response preview
        if result["success"] and result["response"]:
            response_preview = json.dumps(result["response"])[:100] + "..."
        else:
            response_preview = result.get("error", "No response")
        
        # Print results
        status = "✅" if result["success"] else "❌"
        print(f"  {status} Status: {'Success' if result['success'] else 'Failed'}")
        print(f"  📊 Score: {score}/100")
        print(f"  ⏱️  Latency: {result['latency_ms']:.0f}ms")
        print(f"  📝 Response: {response_preview}")
        
        # Store detailed result
        all_results.append({
            "question_id": question["id"],
            "question": question["question"],
            "persona": question["persona"],
            "category": question["category"],
            "success": result["success"],
            "score": score,
            "latency_ms": result["latency_ms"],
            "response": result["response"] if result["success"] else None,
            "error": result.get("error")
        })
        
        # Update persona stats
        persona = question["persona"]
        persona_stats[persona]["total"] += 1
        persona_stats[persona]["scores"].append(score)
        persona_stats[persona]["latencies"].append(result["latency_ms"])
        if result["success"]:
            persona_stats[persona]["successes"] += 1
        
        # Rate limiting
        time.sleep(0.1)
        
        # Progress indicator every 10 questions
        if (i + 1) % 10 == 0:
            print(f"\n{'='*80}")
            print(f"Progress: {i+1}/200 questions completed ({(i+1)/200*100:.1f}%)")
            print(f"{'='*80}")
    
    # Generate comprehensive report
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("="*80)
    
    # Overall statistics
    all_scores = [r["score"] for r in all_results]
    all_latencies = [r["latency_ms"] for r in all_results if r["latency_ms"] > 0]
    successful_tests = sum(1 for r in all_results if r["success"])
    
    print("\n📈 OVERALL STATISTICS:")
    print(f"  Total Questions: {len(all_results)}")
    print(f"  Success Rate: {successful_tests}/{len(all_results)} ({successful_tests/len(all_results)*100:.1f}%)")
    print(f"  Average Score: {statistics.mean(all_scores):.1f}/100")
    print(f"  Median Score: {statistics.median(all_scores):.1f}/100")
    print(f"  Min Score: {min(all_scores):.1f}/100")
    print(f"  Max Score: {max(all_scores):.1f}/100")
    
    if all_latencies:
        print(f"\n⏱️  LATENCY STATISTICS:")
        print(f"  Average: {statistics.mean(all_latencies):.0f}ms")
        print(f"  Median: {statistics.median(all_latencies):.0f}ms")
        print(f"  Min: {min(all_latencies):.0f}ms")
        print(f"  Max: {max(all_latencies):.0f}ms")
        print(f"  95th Percentile: {sorted(all_latencies)[int(len(all_latencies)*0.95)]:.0f}ms")
    
    print("\n👥 PERSONA PERFORMANCE:")
    for persona, stats in persona_stats.items():
        if stats["total"] > 0:
            avg_score = statistics.mean(stats["scores"]) if stats["scores"] else 0
            avg_latency = statistics.mean(stats["latencies"]) if stats["latencies"] else 0
            success_rate = stats["successes"] / stats["total"] * 100
            
            print(f"\n  {persona.replace('_', ' ').title()}:")
            print(f"    Questions: {stats['total']}")
            print(f"    Success Rate: {success_rate:.1f}%")
            print(f"    Avg Score: {avg_score:.1f}/100")
            print(f"    Avg Latency: {avg_latency:.0f}ms")
    
    # Grade distribution
    grade_distribution = {
        "A (90-100)": sum(1 for s in all_scores if s >= 90),
        "B (80-89)": sum(1 for s in all_scores if 80 <= s < 90),
        "C (70-79)": sum(1 for s in all_scores if 70 <= s < 80),
        "D (60-69)": sum(1 for s in all_scores if 60 <= s < 70),
        "F (0-59)": sum(1 for s in all_scores if s < 60)
    }
    
    print("\n📊 GRADE DISTRIBUTION:")
    for grade, count in grade_distribution.items():
        percentage = count / len(all_scores) * 100
        bar = "█" * int(percentage / 2)
        print(f"  {grade}: {bar} {count} ({percentage:.1f}%)")
    
    # Find worst performing questions
    worst_questions = sorted(all_results, key=lambda x: x["score"])[:10]
    
    print("\n⚠️  WORST PERFORMING QUESTIONS (Bottom 10):")
    for i, q in enumerate(worst_questions, 1):
        print(f"  {i}. [{q['question_id']}] {q['question'][:50]}...")
        print(f"     Score: {q['score']}/100, Latency: {q['latency_ms']:.0f}ms")
    
    # Find best performing questions
    best_questions = sorted(all_results, key=lambda x: x["score"], reverse=True)[:10]
    
    print("\n✨ BEST PERFORMING QUESTIONS (Top 10):")
    for i, q in enumerate(best_questions, 1):
        print(f"  {i}. [{q['question_id']}] {q['question'][:50]}...")
        print(f"     Score: {q['score']}/100, Latency: {q['latency_ms']:.0f}ms")
    
    # Save detailed results to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"fact_test_200_results_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump({
            "test_metadata": {
                "timestamp": timestamp,
                "total_questions": len(all_results),
                "endpoint": WEBHOOK_URL
            },
            "summary": {
                "success_rate": successful_tests / len(all_results),
                "average_score": statistics.mean(all_scores),
                "median_score": statistics.median(all_scores),
                "average_latency_ms": statistics.mean(all_latencies) if all_latencies else 0
            },
            "persona_performance": {
                persona: {
                    "total": stats["total"],
                    "success_rate": stats["successes"] / stats["total"] if stats["total"] > 0 else 0,
                    "average_score": statistics.mean(stats["scores"]) if stats["scores"] else 0,
                    "average_latency_ms": statistics.mean(stats["latencies"]) if stats["latencies"] else 0
                }
                for persona, stats in persona_stats.items()
            },
            "grade_distribution": grade_distribution,
            "all_results": all_results
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    # Final summary
    print("\n" + "="*80)
    print("🏁 TEST COMPLETE")
    print("="*80)
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Overall grade
    avg_score = statistics.mean(all_scores)
    if avg_score >= 90:
        grade = "A - Excellent"
    elif avg_score >= 80:
        grade = "B - Good"
    elif avg_score >= 70:
        grade = "C - Satisfactory"
    elif avg_score >= 60:
        grade = "D - Needs Improvement"
    else:
        grade = "F - Poor"
    
    print(f"\n🎯 OVERALL SYSTEM GRADE: {grade}")
    print(f"   Score: {avg_score:.1f}/100")

if __name__ == "__main__":
    main()
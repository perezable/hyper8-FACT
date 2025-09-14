#!/usr/bin/env python3
"""
Comprehensive FACT System Test with 200 Questions
Tests the REAL production system and logs all Q&A details
"""

import json
import requests
import time
from datetime import datetime
import statistics
import sys

# Production webhook endpoint (requires real responses)
WEBHOOK_URL = "https://hyper8-fact-fact-system.up.railway.app/vapi-enhanced/webhook"

# For testing without auth, we'll use a different approach
SEARCH_URL = "https://hyper8-fact-fact-system.up.railway.app/knowledge/search"
HEALTH_URL = "https://hyper8-fact-fact-system.up.railway.app/health"

def generate_200_questions():
    """Generate comprehensive test questions across all personas"""
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
            "id": f"pc_{i+1:03d}",
            "question": q,
            "persona": "price_conscious",
            "category": "cost" if any(word in q.lower() for word in ["cost", "price", "$", "fee", "investment"]) else "general"
        })
    
    for i, q in enumerate(overwhelmed):
        questions.append({
            "id": f"ov_{i+1:03d}",
            "question": q,
            "persona": "overwhelmed_veteran",
            "category": "process" if any(word in q.lower() for word in ["process", "step", "how"]) else "requirements"
        })
    
    for i, q in enumerate(skeptical):
        questions.append({
            "id": f"sr_{i+1:03d}",
            "question": q,
            "persona": "skeptical_researcher",
            "category": "validation" if any(word in q.lower() for word in ["prove", "data", "evidence"]) else "statistics"
        })
    
    for i, q in enumerate(time_pressed):
        questions.append({
            "id": f"tp_{i+1:03d}",
            "question": q,
            "persona": "time_pressed",
            "category": "timeline" if any(word in q.lower() for word in ["fast", "quick", "expedite"]) else "process"
        })
    
    for i, q in enumerate(ambitious):
        questions.append({
            "id": f"ae_{i+1:03d}",
            "question": q,
            "persona": "ambitious_entrepreneur",
            "category": "growth" if any(word in q.lower() for word in ["expand", "scale", "grow"]) else "opportunity"
        })
    
    return questions

def query_fact_system(question_text):
    """Query the FACT system using the search endpoint"""
    try:
        start_time = time.time()
        
        # Try the search endpoint first
        response = requests.post(
            SEARCH_URL,
            json={"query": question_text, "limit": 3},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            # Extract the best answer
            if results:
                best_answer = results[0].get('answer', 'No answer found')
                return {
                    "success": True,
                    "answer": best_answer,
                    "full_response": data,
                    "latency_ms": latency_ms,
                    "status_code": 200
                }
            else:
                return {
                    "success": False,
                    "answer": "No results found",
                    "full_response": data,
                    "latency_ms": latency_ms,
                    "status_code": 200
                }
        else:
            return {
                "success": False,
                "answer": f"Error: HTTP {response.status_code}",
                "full_response": None,
                "latency_ms": latency_ms,
                "status_code": response.status_code
            }
            
    except requests.Timeout:
        return {
            "success": False,
            "answer": "Timeout after 10 seconds",
            "full_response": None,
            "latency_ms": 10000,
            "status_code": 0
        }
    except Exception as e:
        return {
            "success": False,
            "answer": f"Error: {str(e)}",
            "full_response": None,
            "latency_ms": 0,
            "status_code": 0
        }

def score_response(question, result):
    """Score the response quality (0-100)"""
    if not result["success"]:
        return 0
    
    score = 0
    answer = result["answer"].lower() if result["answer"] else ""
    
    # Base score for having an answer (40 points)
    if answer and answer != "no results found" and answer != "no answer found":
        score += 40
    
    # Content relevance (30 points)
    question_text = question["question"].lower()
    
    # Check for keyword matches
    keywords = question_text.split()
    matches = sum(1 for keyword in keywords if len(keyword) > 3 and keyword in answer)
    if matches > 0:
        score += min(30, matches * 5)
    
    # Response time scoring (20 points)
    if result["latency_ms"] < 200:
        score += 20
    elif result["latency_ms"] < 500:
        score += 15
    elif result["latency_ms"] < 1000:
        score += 10
    elif result["latency_ms"] < 2000:
        score += 5
    
    # Persona-specific scoring (10 points)
    persona = question["persona"]
    if persona == "price_conscious":
        if any(word in answer for word in ["cost", "price", "$", "fee", "investment", "affordable"]):
            score += 10
    elif persona == "overwhelmed_veteran":
        if any(word in answer for word in ["help", "step", "guide", "simple", "easy", "support"]):
            score += 10
    elif persona == "skeptical_researcher":
        if any(word in answer for word in ["data", "rate", "%", "success", "proof", "evidence"]):
            score += 10
    elif persona == "time_pressed":
        if any(word in answer for word in ["fast", "quick", "expedite", "rush", "day", "week"]):
            score += 10
    elif persona == "ambitious_entrepreneur":
        if any(word in answer for word in ["expand", "scale", "grow", "income", "opportunity", "commercial"]):
            score += 10
    
    return min(score, 100)

def main():
    print("\n" + "="*80)
    print("🚀 FACT SYSTEM COMPREHENSIVE TEST - 200 QUESTIONS")
    print("="*80)
    print(f"Endpoint: {SEARCH_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Check system health first
    try:
        health_response = requests.get(HEALTH_URL, timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            entries = health_data.get("metrics", {}).get("enhanced_retriever_entries", 0)
            print(f"\n✅ System Status: HEALTHY")
            print(f"📊 Knowledge Entries: {entries}")
        else:
            print(f"\n⚠️  System Status: UNKNOWN")
    except:
        print(f"\n⚠️  Could not check system status")
    
    # Generate questions
    questions = generate_200_questions()
    print(f"\n📝 Testing {len(questions)} questions across 5 personas")
    
    # Results storage
    test_results = {
        "test_metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_questions": len(questions),
            "endpoint": SEARCH_URL
        },
        "questions_and_answers": [],
        "summary": {},
        "persona_performance": {},
        "grade_distribution": {}
    }
    
    # Track metrics
    all_scores = []
    all_latencies = []
    persona_stats = {}
    
    print("\n🔬 Testing each question...")
    print("-"*80)
    
    # Test each question
    for i, question in enumerate(questions):
        # Query the system
        result = query_fact_system(question["question"])
        
        # Score the response
        score = score_response(question, result)
        
        # Store detailed result
        qa_entry = {
            "question_id": question["id"],
            "question": question["question"],
            "answer": result["answer"],
            "persona": question["persona"],
            "category": question["category"],
            "score": score,
            "latency_ms": result["latency_ms"],
            "success": result["success"]
        }
        test_results["questions_and_answers"].append(qa_entry)
        
        # Update statistics
        all_scores.append(score)
        if result["latency_ms"] > 0:
            all_latencies.append(result["latency_ms"])
        
        # Track by persona
        persona = question["persona"]
        if persona not in persona_stats:
            persona_stats[persona] = {"scores": [], "latencies": [], "successes": 0, "total": 0}
        persona_stats[persona]["scores"].append(score)
        persona_stats[persona]["latencies"].append(result["latency_ms"])
        persona_stats[persona]["total"] += 1
        if result["success"]:
            persona_stats[persona]["successes"] += 1
        
        # Progress output
        if (i + 1) % 10 == 0:
            avg_score = statistics.mean(all_scores)
            print(f"Progress: {i+1}/{len(questions)} | Avg Score: {avg_score:.1f} | Last: {question['id']} = {score}/100")
        
        # Rate limiting
        time.sleep(0.1)
    
    # Calculate summary statistics
    successful_tests = sum(1 for qa in test_results["questions_and_answers"] if qa["success"])
    
    test_results["summary"] = {
        "total_questions": len(questions),
        "successful_queries": successful_tests,
        "success_rate": successful_tests / len(questions),
        "average_score": statistics.mean(all_scores),
        "median_score": statistics.median(all_scores),
        "min_score": min(all_scores),
        "max_score": max(all_scores),
        "average_latency_ms": statistics.mean(all_latencies) if all_latencies else 0,
        "median_latency_ms": statistics.median(all_latencies) if all_latencies else 0
    }
    
    # Persona performance
    for persona, stats in persona_stats.items():
        test_results["persona_performance"][persona] = {
            "total_questions": stats["total"],
            "success_rate": stats["successes"] / stats["total"] if stats["total"] > 0 else 0,
            "average_score": statistics.mean(stats["scores"]) if stats["scores"] else 0,
            "average_latency_ms": statistics.mean(stats["latencies"]) if stats["latencies"] else 0
        }
    
    # Grade distribution
    test_results["grade_distribution"] = {
        "A (90-100)": sum(1 for s in all_scores if s >= 90),
        "B (80-89)": sum(1 for s in all_scores if 80 <= s < 90),
        "C (70-79)": sum(1 for s in all_scores if 70 <= s < 80),
        "D (60-69)": sum(1 for s in all_scores if 60 <= s < 70),
        "F (0-59)": sum(1 for s in all_scores if s < 60)
    }
    
    # Save complete results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"comprehensive_fact_test_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    # Print summary
    print("\n" + "="*80)
    print("📊 TEST COMPLETE - SUMMARY")
    print("="*80)
    print(f"✅ Success Rate: {test_results['summary']['success_rate']*100:.1f}%")
    print(f"📈 Average Score: {test_results['summary']['average_score']:.1f}/100")
    print(f"⏱️  Average Latency: {test_results['summary']['average_latency_ms']:.0f}ms")
    
    print("\n👥 Persona Performance:")
    for persona, perf in test_results["persona_performance"].items():
        print(f"  {persona}: {perf['average_score']:.1f}/100")
    
    print(f"\n💾 Complete results saved to: {output_file}")
    print(f"   File contains all {len(questions)} questions with answers and scores")
    
    # Calculate overall grade
    avg_score = test_results['summary']['average_score']
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
    
    print(f"\n🎯 OVERALL GRADE: {grade} ({avg_score:.1f}/100)")

if __name__ == "__main__":
    main()
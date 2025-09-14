#!/usr/bin/env python3
"""
Comprehensive Enhanced Test Suite for FACT System
Tests with 200 questions across 5 personas after knowledge base update to 1,347 entries
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple
import statistics

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

# Enhanced test questions covering all personas and scenarios
TEST_QUESTIONS = {
    "price_conscious": [
        # Cost and pricing questions
        "What's the cheapest state to get a contractor license?",
        "How much does a Florida contractor license cost total?",
        "Are there payment plans available for licensing fees?",
        "What financing options does CLP offer?",
        "How much is the California contractor bond?",
        "What's the cost difference between LLC and sole proprietor licensing?",
        "Can I get a discount for multiple state licenses?",
        "What are the hidden fees in contractor licensing?",
        "How much does license renewal cost?",
        "What's the ROI on getting licensed?",
        "Are there any states with no licensing fees?",
        "How much do exam retakes cost?",
        "What's the average cost across all states?",
        "Can I deduct licensing costs on taxes?",
        "How much does workers comp insurance cost?",
        "What's the cheapest bond option?",
        "Do veterans get discounts?",
        "What payment methods are accepted?",
        "How much does the NASCLA exam cost?",
        "What's included in the $1,400 CLP fee?",
        "Are state fees marked up?",
        "Can I pay monthly instead of upfront?",
        "What's the total cost for Texas licensing?",
        "How much for registered agent service?",
        "What are continuing education costs?",
        "Is there a money-back guarantee?",
        "How much to add a second classification?",
        "What's the cost for reciprocity applications?",
        "Do prices include everything?",
        "How much is rush processing?",
        "What credit score is needed for financing?",
        "Are there setup fees for payment plans?",
        "How much does bad credit increase costs?",
        "What's the penalty for late renewal?",
        "Can I get a refund if I fail?",
        "How much do background checks cost?",
        "What's the fee for qualifier placement?",
        "Are travel expenses covered?",
        "How much for priority support?",
        "What's the average monthly payment with financing?"
    ],
    
    "overwhelmed_veteran": [
        # Simple, supportive guidance questions
        "I don't know where to start - can you help?",
        "What documents do I need?",
        "Can you walk me through the process step by step?",
        "Is this really complicated?",
        "What if I fail the exam?",
        "How do I know which license I need?",
        "Can someone help me with paperwork?",
        "I'm confused about requirements - help?",
        "Do I need a lawyer?",
        "What's the first step?",
        "How long will this take?",
        "Can I do this myself?",
        "What if I make a mistake?",
        "Who can I call for help?",
        "Is there a checklist I can follow?",
        "What's the easiest state to get licensed?",
        "Can you simplify the process for me?",
        "Do I need experience?",
        "What if I don't have all documents?",
        "Can military experience count?",
        "How do I prove my experience?",
        "What's a qualifying agent?",
        "Do I need insurance first?",
        "Can I work while waiting?",
        "What if I have bad credit?",
        "Do I need a business entity?",
        "What's the difference between licenses?",
        "How do I prepare for the exam?",
        "What if English isn't my first language?",
        "Can family help with application?",
        "What support is available?",
        "How many people fail first time?",
        "What's the hardest part?",
        "Can I change license type later?",
        "Do I need a computer?",
        "What if I have a criminal record?",
        "How do I find study materials?",
        "Can I take breaks during exam?",
        "What happens after I pass?",
        "Is there ongoing help after licensing?"
    ],
    
    "skeptical_researcher": [
        # Data, proof, and validation questions
        "What's your success rate?",
        "How many contractors have you helped?",
        "What states accept NASCLA?",
        "What are the exact requirements for California?",
        "How long have you been in business?",
        "What's your BBB rating?",
        "Can I see testimonials?",
        "What's the first-time pass rate?",
        "How do you compare to competitors?",
        "What are the legal requirements?",
        "Is this legitimate?",
        "What happens if you make an error?",
        "Do you have insurance?",
        "What's your refund policy?",
        "Can I verify your credentials?",
        "What states have reciprocity?",
        "What's the penalty for unlicensed work?",
        "How current is your information?",
        "What percentage need retakes?",
        "Do you guarantee approval?",
        "What's your average processing time?",
        "How many states do you cover?",
        "What's not included in your service?",
        "Can I see a sample application?",
        "What are common rejection reasons?",
        "How do you protect my information?",
        "What's your physical address?",
        "Can I speak to previous clients?",
        "What professional associations are you in?",
        "How do you stay updated on laws?",
        "What's your error rate?",
        "Do you have E&O insurance?",
        "What training do your staff have?",
        "Can I see your business license?",
        "How many applications get rejected?",
        "What's the average time to license?",
        "Do you work with all boards?",
        "What if requirements change?",
        "Can you provide references?",
        "What's your complaint history?"
    ],
    
    "time_pressed": [
        # Speed and urgency questions
        "What's the fastest way to get licensed?",
        "Can I expedite the process?",
        "How quickly can I start working?",
        "What's the shortest timeline?",
        "Can I fast-track my application?",
        "Which state is quickest?",
        "How fast with reciprocity?",
        "Can I work before license arrives?",
        "What about emergency licensing?",
        "How quick is renewal?",
        "Can I get same-day approval?",
        "What's rush processing time?",
        "How fast can I schedule exam?",
        "What if I need license tomorrow?",
        "Can you expedite paperwork?",
        "What's priority processing?",
        "How long for temp license?",
        "Fastest state for veterans?",
        "Can I start bidding immediately?",
        "What's electronic filing time?",
        "How quick is online exam?",
        "Can I skip waiting periods?",
        "What about provisional licenses?",
        "How fast is qualifier placement?",
        "Can multiple states be done together?",
        "What's weekend processing like?",
        "How quick for second license?",
        "Can I pay for faster service?",
        "What's holiday processing time?",
        "How fast is reciprocity?",
        "Can exam be waived?",
        "What's digital license time?",
        "How quick with perfect paperwork?",
        "Can board meetings be expedited?",
        "What about emergency projects?",
        "How fast for simple renewal?",
        "Can I get temporary approval?",
        "What's the fastest you've done?",
        "How quick for LLC formation?",
        "What if I have a deadline?"
    ],
    
    "ambitious_entrepreneur": [
        # Growth and expansion questions
        "How do I get licensed in multiple states?",
        "What's the best license for growth?",
        "Can I qualify other companies?",
        "How do I maximize income?",
        "What about nationwide licensing?",
        "Best states for contractors?",
        "How to build a contractor empire?",
        "What licenses command highest fees?",
        "Can I get all specialty licenses?",
        "What about government contracts?",
        "How to become a GC?",
        "Best license for commercial work?",
        "Can I broker licenses?",
        "What's qualifier income potential?",
        "How to expand quickly?",
        "Best reciprocity strategy?",
        "Can I franchise with license?",
        "What about international work?",
        "How to get federal contracts?",
        "Best license combinations?",
        "Can I sell my license?",
        "What about license leasing?",
        "How to get on state boards?",
        "Best markets for contractors?",
        "Can I mentor others?",
        "What's the most valuable license?",
        "How to become preferred contractor?",
        "Best insurance for growth?",
        "Can I get investor funding?",
        "What about contractor associations?",
        "How to get union contracts?",
        "Best CRM for contractors?",
        "Can I automate licensing?",
        "What about contractor coaching?",
        "How to build contractor network?",
        "Best exit strategy?",
        "Can I go public?",
        "What about acquisition targets?",
        "How to value contractor business?",
        "Best growth markets 2024?"
    ]
}

async def test_query(session: aiohttp.ClientSession, question: str) -> Dict:
    """Test a single query against the FACT system"""
    start_time = time.time()
    
    try:
        payload = {
            "query": question,
            "context": "Contractor licensing inquiry",
            "include_sources": True
        }
        
        async with session.post(
            f"{RAILWAY_URL}/query",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            latency = (time.time() - start_time) * 1000  # Convert to ms
            
            if response.status == 200:
                data = await response.json()
                return {
                    "question": question,
                    "answer": data.get("answer", ""),
                    "sources": data.get("sources", []),
                    "latency": latency,
                    "status": "success",
                    "confidence": data.get("confidence", 0)
                }
            else:
                return {
                    "question": question,
                    "answer": "",
                    "error": f"HTTP {response.status}",
                    "latency": latency,
                    "status": "error"
                }
                
    except asyncio.TimeoutError:
        return {
            "question": question,
            "answer": "",
            "error": "Timeout",
            "latency": 10000,
            "status": "timeout"
        }
    except Exception as e:
        return {
            "question": question,
            "answer": "",
            "error": str(e),
            "latency": (time.time() - start_time) * 1000,
            "status": "error"
        }

def score_response(question: str, answer: str, persona: str) -> float:
    """Score a response based on quality criteria"""
    if not answer or answer == "":
        return 0.0
    
    score = 0.0
    
    # Base scoring criteria
    if len(answer) > 50:
        score += 20  # Has substance
    if len(answer) > 200:
        score += 10  # Detailed response
    
    # Check for specific keywords based on persona
    persona_keywords = {
        "price_conscious": ["cost", "price", "$", "fee", "payment", "financing", "discount", "save"],
        "overwhelmed_veteran": ["help", "support", "simple", "easy", "step", "guide", "assist", "we"],
        "skeptical_researcher": ["data", "rate", "%", "statistics", "proven", "verified", "guarantee"],
        "time_pressed": ["fast", "quick", "immediate", "day", "hour", "rush", "expedite", "priority"],
        "ambitious_entrepreneur": ["growth", "expand", "multiple", "income", "scale", "maximize", "profit"]
    }
    
    keywords_found = sum(1 for keyword in persona_keywords.get(persona, []) 
                        if keyword.lower() in answer.lower())
    score += min(keywords_found * 5, 30)  # Up to 30 points for keywords
    
    # Check for specific data points
    if any(char.isdigit() for char in answer):
        score += 10  # Contains numbers/data
    
    # Check for actionable information
    action_words = ["call", "visit", "apply", "submit", "contact", "schedule", "start", "click"]
    if any(word in answer.lower() for word in action_words):
        score += 10  # Actionable
    
    # Check for CLP/FACT specific information
    if "clp" in answer.lower() or "contractor licensing pros" in answer.lower():
        score += 10  # Brand-specific
    
    # Penalty for generic or unhelpful responses
    if "i don't know" in answer.lower() or "not sure" in answer.lower():
        score -= 20
    if len(answer) < 30:
        score -= 10  # Too brief
    
    # Ensure score is between 0 and 100
    return max(0, min(100, score))

async def run_comprehensive_test():
    """Run comprehensive test with all questions"""
    print("\n" + "="*70)
    print("🚀 COMPREHENSIVE FACT SYSTEM TEST - ENHANCED KNOWLEDGE BASE")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL: {RAILWAY_URL}")
    print(f"Total Questions: 200")
    print(f"Personas: 5")
    print("\nStarting test...\n")
    
    results = {}
    all_results = []
    
    async with aiohttp.ClientSession() as session:
        # Test each persona
        for persona, questions in TEST_QUESTIONS.items():
            print(f"Testing {persona} persona ({len(questions)} questions)...")
            persona_results = []
            
            # Test questions in batches for efficiency
            batch_size = 5
            for i in range(0, len(questions), batch_size):
                batch = questions[i:i+batch_size]
                tasks = [test_query(session, q) for q in batch]
                batch_results = await asyncio.gather(*tasks)
                
                # Score each result
                for result in batch_results:
                    if result["status"] == "success":
                        score = score_response(
                            result["question"], 
                            result.get("answer", ""),
                            persona
                        )
                        result["score"] = score
                    else:
                        result["score"] = 0
                    
                    result["persona"] = persona
                    persona_results.append(result)
                    all_results.append(result)
                
                # Progress indicator
                if (i + batch_size) % 10 == 0:
                    print(f"  Processed {min(i + batch_size, len(questions))}/{len(questions)} questions")
            
            results[persona] = persona_results
    
    return results, all_results

def analyze_results(results: Dict, all_results: List) -> Dict:
    """Analyze test results and generate statistics"""
    
    # Overall statistics
    total_questions = len(all_results)
    successful_queries = sum(1 for r in all_results if r["status"] == "success")
    failed_queries = sum(1 for r in all_results if r["status"] != "success")
    
    # Score statistics
    scores = [r["score"] for r in all_results if "score" in r]
    avg_score = statistics.mean(scores) if scores else 0
    median_score = statistics.median(scores) if scores else 0
    
    # Latency statistics
    latencies = [r["latency"] for r in all_results if r["status"] == "success"]
    avg_latency = statistics.mean(latencies) if latencies else 0
    median_latency = statistics.median(latencies) if latencies else 0
    
    # Persona-specific analysis
    persona_stats = {}
    for persona, persona_results in results.items():
        persona_scores = [r["score"] for r in persona_results if "score" in r]
        persona_latencies = [r["latency"] for r in persona_results if r["status"] == "success"]
        
        persona_stats[persona] = {
            "total_questions": len(persona_results),
            "successful": sum(1 for r in persona_results if r["status"] == "success"),
            "failed": sum(1 for r in persona_results if r["status"] != "success"),
            "avg_score": statistics.mean(persona_scores) if persona_scores else 0,
            "median_score": statistics.median(persona_scores) if persona_scores else 0,
            "min_score": min(persona_scores) if persona_scores else 0,
            "max_score": max(persona_scores) if persona_scores else 0,
            "avg_latency": statistics.mean(persona_latencies) if persona_latencies else 0,
            "success_rate": (sum(1 for r in persona_results if r["status"] == "success") / 
                           len(persona_results) * 100) if persona_results else 0
        }
    
    # Find best and worst performing questions
    sorted_results = sorted(all_results, key=lambda x: x.get("score", 0))
    worst_10 = sorted_results[:10]
    best_10 = sorted_results[-10:]
    
    return {
        "summary": {
            "total_questions": total_questions,
            "successful_queries": successful_queries,
            "failed_queries": failed_queries,
            "success_rate": (successful_queries / total_questions * 100) if total_questions > 0 else 0,
            "avg_score": avg_score,
            "median_score": median_score,
            "avg_latency": avg_latency,
            "median_latency": median_latency
        },
        "persona_stats": persona_stats,
        "worst_performing": worst_10,
        "best_performing": best_10
    }

def generate_report(results: Dict, all_results: List, analysis: Dict):
    """Generate detailed performance report"""
    
    report = []
    report.append("\n" + "="*70)
    report.append("📊 COMPREHENSIVE TEST RESULTS - ENHANCED KNOWLEDGE BASE")
    report.append("="*70)
    report.append(f"Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Knowledge Base Size: 1,347 entries")
    
    # Overall Summary
    report.append("\n🎯 OVERALL PERFORMANCE")
    report.append("-" * 40)
    summary = analysis["summary"]
    report.append(f"Total Questions Tested: {summary['total_questions']}")
    report.append(f"Successful Queries: {summary['successful_queries']} ({summary['success_rate']:.1f}%)")
    report.append(f"Failed Queries: {summary['failed_queries']}")
    report.append(f"Average Score: {summary['avg_score']:.1f}/100")
    report.append(f"Median Score: {summary['median_score']:.1f}/100")
    report.append(f"Average Latency: {summary['avg_latency']:.0f}ms")
    report.append(f"Median Latency: {summary['median_latency']:.0f}ms")
    
    # Grade assignment
    avg_score = summary['avg_score']
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
    report.append(f"\n📈 Overall Grade: {grade} ({avg_score:.1f}/100)")
    
    # Persona Performance
    report.append("\n👥 PERSONA PERFORMANCE")
    report.append("-" * 40)
    
    for persona, stats in analysis["persona_stats"].items():
        report.append(f"\n{persona.replace('_', ' ').title()}:")
        report.append(f"  Average Score: {stats['avg_score']:.1f}/100")
        report.append(f"  Success Rate: {stats['success_rate']:.1f}%")
        report.append(f"  Avg Latency: {stats['avg_latency']:.0f}ms")
        report.append(f"  Score Range: {stats['min_score']:.0f}-{stats['max_score']:.0f}")
    
    # Top Performing Questions
    report.append("\n✅ TOP 10 BEST PERFORMING QUESTIONS")
    report.append("-" * 40)
    for i, result in enumerate(analysis["best_performing"], 1):
        report.append(f"{i}. [{result['score']:.0f}/100] {result['question'][:60]}...")
        if len(result.get('answer', '')) > 0:
            report.append(f"   Answer preview: {result['answer'][:100]}...")
    
    # Worst Performing Questions
    report.append("\n❌ TOP 10 WORST PERFORMING QUESTIONS")
    report.append("-" * 40)
    for i, result in enumerate(analysis["worst_performing"], 1):
        report.append(f"{i}. [{result['score']:.0f}/100] {result['question'][:60]}...")
        if result.get('error'):
            report.append(f"   Error: {result['error']}")
        elif len(result.get('answer', '')) > 0:
            report.append(f"   Answer preview: {result['answer'][:100]}...")
    
    return "\n".join(report)

async def main():
    """Main test execution"""
    
    # Run comprehensive test
    results, all_results = await run_comprehensive_test()
    
    # Analyze results
    analysis = analyze_results(results, all_results)
    
    # Generate report
    report = generate_report(results, all_results, analysis)
    
    # Print report
    print(report)
    
    # Save detailed results to JSON
    output_file = f"comprehensive_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "metadata": {
                "test_date": datetime.now().isoformat(),
                "knowledge_base_entries": 1347,
                "total_questions": len(all_results),
                "railway_url": RAILWAY_URL
            },
            "summary": analysis["summary"],
            "persona_stats": analysis["persona_stats"],
            "all_results": all_results
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    # Comparison with previous test
    print("\n📊 COMPARISON WITH PREVIOUS TEST")
    print("-" * 40)
    print("Previous Test (1,055 entries):")
    print("  Average Score: 67.7/100")
    print("  Success Rate: 100%")
    print("  Overwhelmed Veteran: 62.5/100")
    print("")
    print(f"Current Test (1,347 entries):")
    print(f"  Average Score: {analysis['summary']['avg_score']:.1f}/100")
    print(f"  Success Rate: {analysis['summary']['success_rate']:.1f}%")
    print(f"  Overwhelmed Veteran: {analysis['persona_stats']['overwhelmed_veteran']['avg_score']:.1f}/100")
    
    # Calculate improvements
    prev_score = 67.7
    curr_score = analysis['summary']['avg_score']
    improvement = curr_score - prev_score
    
    prev_ov_score = 62.5
    curr_ov_score = analysis['persona_stats']['overwhelmed_veteran']['avg_score']
    ov_improvement = curr_ov_score - prev_ov_score
    
    print("")
    print("📈 Improvements:")
    print(f"  Overall Score: {'+' if improvement >= 0 else ''}{improvement:.1f} points")
    print(f"  Overwhelmed Veteran: {'+' if ov_improvement >= 0 else ''}{ov_improvement:.1f} points")
    
    return analysis

if __name__ == "__main__":
    asyncio.run(main())
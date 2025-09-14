#!/usr/bin/env python3
"""
Demo script for FACT System Automated Testing Framework

Shows how to use the testing framework with a small sample test.
"""

import asyncio
import sys
from pathlib import Path

# Add tests directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fact_test_runner import FACTTestRunner, TestConfig
from synthetic_questions import SyntheticQuestionGenerator
from query_executor import TestQuestion


async def demo_testing_framework():
    """Demonstrate the testing framework capabilities"""
    print("🧪 FACT System Testing Framework Demo")
    print("=" * 50)
    
    # 1. Generate sample questions
    print("1. Generating sample test questions...")
    generator = SyntheticQuestionGenerator()
    
    questions = await generator.generate_questions(count=10)
    print(f"   ✅ Generated {len(questions)} questions")
    
    # Show sample questions
    print("\n   Sample questions:")
    for i, q in enumerate(questions[:3], 1):
        print(f"   {i}. [{q.category}] {q.text}")
    
    # 2. Create test configuration
    print("\n2. Creating test configuration...")
    config = TestConfig(
        environment="demo",
        database_url="sqlite:///data/fact_system.db",
        api_base_url="http://localhost:8000",
        vapi_webhook_url="http://localhost:8000/vapi/webhook",
        max_concurrent_tests=3,
        request_timeout=15,
        query_methods=["database"],  # Only test database for demo
        test_question_count=5,
        questions_per_batch=5,
        output_dir="test_results/demo"
    )
    print("   ✅ Configuration created")
    
    # 3. Initialize test runner
    print("\n3. Initializing test runner...")
    test_runner = FACTTestRunner(config)
    
    try:
        # Override questions with our demo set
        test_runner.test_questions = questions[:5]  # Use first 5 questions
        
        # Show what we're testing
        print("\n   Demo test questions:")
        for i, q in enumerate(test_runner.test_questions, 1):
            print(f"   {i}. {q.text[:60]}...")
        
        print("\n4. Running demo test (database queries only)...")
        print("   This will test the FACT system's ability to respond to questions")
        print("   and evaluate response quality.")
        
        # Initialize components individually for demo
        await test_runner.query_executor.initialize()
        await test_runner.response_collector.initialize()
        
        # Run a simple test with just database method
        from query_executor import QueryMethod
        
        results = []
        for i, question in enumerate(test_runner.test_questions, 1):
            print(f"\n   Testing question {i}/5: {question.text[:50]}...")
            
            try:
                # Execute query
                result = await test_runner.query_executor.execute_query(
                    QueryMethod.DATABASE, question
                )
                
                # Collect and evaluate result
                test_result = await test_runner.response_collector.collect_result(
                    {
                        'query_id': result.query_id,
                        'question_id': question.id,
                        'query_text': question.text,
                        'method': result.method,
                        'success': result.success,
                        'response': result.response,
                        'response_time_ms': result.response_time_ms,
                        'error_message': result.error_message,
                        'attempt_count': result.attempt_count,
                        'timestamp': result.timestamp.isoformat()
                    },
                    expected_category=question.category,
                    expected_state=question.state
                )
                
                results.append(test_result)
                
                # Show result
                if test_result.success:
                    print(f"      ✅ Success! Response time: {test_result.response_time_ms:.1f}ms")
                    if test_result.accuracy_score:
                        print(f"      📊 Accuracy: {test_result.accuracy_score:.2f}")
                    if test_result.response and test_result.response.get('answer'):
                        answer = test_result.response['answer'][:100]
                        print(f"      💬 Answer: {answer}...")
                else:
                    print(f"      ❌ Failed: {test_result.error_message}")
                    
            except Exception as e:
                print(f"      💥 Error: {e}")
        
        # 5. Generate summary
        print(f"\n5. Demo Results Summary")
        print("   " + "-" * 30)
        
        successful_results = [r for r in results if r.success]
        success_rate = len(successful_results) / len(results) if results else 0
        
        if successful_results:
            avg_response_time = sum(r.response_time_ms for r in successful_results) / len(successful_results)
            accuracy_scores = [r.accuracy_score for r in successful_results if r.accuracy_score]
            avg_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0
            
            print(f"   Total Questions: {len(results)}")
            print(f"   Success Rate: {success_rate:.1%}")
            print(f"   Average Response Time: {avg_response_time:.1f}ms")
            print(f"   Average Accuracy: {avg_accuracy:.2f}")
            
            # Performance assessment
            if success_rate >= 0.8:
                print("   🎉 System Performance: GOOD")
            elif success_rate >= 0.6:
                print("   ⚠️  System Performance: FAIR")  
            else:
                print("   🚨 System Performance: POOR")
        else:
            print("   ❌ No successful queries")
        
        print(f"\n✅ Demo completed! Check test_results/demo/ for detailed results.")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        raise
    finally:
        await test_runner.cleanup()


async def show_framework_capabilities():
    """Show framework capabilities without running tests"""
    print("🔧 FACT Testing Framework Capabilities")
    print("=" * 50)
    
    print("✨ Multi-Method Testing:")
    print("   • Database queries (direct SQLite/PostgreSQL)")
    print("   • VAPI webhook calls (searchKnowledge function)")
    print("   • REST API endpoints (/search, /api/search)")
    
    print("\n⚡ Parallel Execution:")
    print("   • Concurrent request processing")
    print("   • Intelligent load balancing")
    print("   • Rate limiting and retry logic")
    
    print("\n🎯 Question Categories:")
    categories = [
        "State Licensing Requirements",
        "Exam Preparation & Testing", 
        "Qualifier Network Programs",
        "Business Formation & Operations",
        "Insurance & Bonding",
        "Financial Planning & ROI",
        "Success Stories & Case Studies",
        "Troubleshooting & Problem Resolution"
    ]
    
    for category in categories:
        print(f"   • {category}")
    
    print("\n📊 Evaluation Metrics:")
    print("   • Accuracy Score (keyword matching, domain relevance)")
    print("   • Relevance Score (category matching, context)")
    print("   • Completeness Score (detail level, structure)")
    print("   • Performance Metrics (response time, throughput)")
    
    print("\n🎮 Available Commands:")
    commands = [
        ("python tests/run_tests.py quick", "Quick 20-question validation"),
        ("python tests/run_tests.py local", "Full 200-question local test"),
        ("python tests/run_tests.py railway", "Production testing"),
        ("python tests/run_tests.py database", "Database method only"),
        ("python tests/run_tests.py questions", "Generate question sets")
    ]
    
    for cmd, desc in commands:
        print(f"   • {cmd}")
        print(f"     {desc}")


async def main():
    """Main entry point"""
    print("Welcome to the FACT System Testing Framework!\n")
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="Run demo test")
    parser.add_argument("--show", action="store_true", help="Show capabilities")
    args = parser.parse_args()
    
    if args.demo:
        await demo_testing_framework()
    elif args.show:
        await show_framework_capabilities()
    else:
        print("Usage:")
        print("  python demo_test_framework.py --demo   # Run demo test")
        print("  python demo_test_framework.py --show   # Show capabilities")
        print("\nFor full testing options:")
        print("  python run_tests.py help")


if __name__ == "__main__":
    asyncio.run(main())
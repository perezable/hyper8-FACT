#!/usr/bin/env python3
"""
FACT System Test Runner Entry Point

Convenience script for running automated tests with predefined configurations.
Supports local, Railway production, and performance testing scenarios.
"""

import asyncio
import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add tests directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from fact_test_runner import FACTTestRunner, TestConfig
from query_executor import QueryMethod

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_environment():
    """Setup environment for testing"""
    # Create necessary directories
    test_dirs = [
        'test_results',
        'test_results/local',
        'test_results/railway', 
        'test_results/performance'
    ]
    
    for dir_path in test_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    logger.info("Test environment setup complete")


async def run_local_tests():
    """Run comprehensive local testing"""
    print("🔧 Running Local FACT System Tests")
    print("=" * 50)
    
    config_path = Path(__file__).parent / "configs" / "local_test_config.yaml"
    config = TestConfig.from_file(str(config_path))
    
    test_runner = FACTTestRunner(config)
    
    try:
        await test_runner.initialize()
        summary = await test_runner.run_comprehensive_test()
        
        print(f"\n✅ Local tests completed!")
        print(f"📊 Results: {summary.overall_metrics['success_rate']:.1%} success rate")
        print(f"⚡ Average response time: {summary.overall_metrics['avg_response_time_ms']:.1f}ms")
        print(f"📁 Results saved to: {config.output_dir}")
        
        return summary
        
    except Exception as e:
        print(f"\n❌ Local tests failed: {e}")
        logger.error(f"Local test error: {e}")
        raise
    finally:
        await test_runner.cleanup()


async def run_railway_tests():
    """Run production testing against Railway deployment"""
    print("🚀 Running Railway Production Tests")
    print("=" * 50)
    
    # Check if DATABASE_URL is available
    if not os.getenv("DATABASE_URL"):
        print("⚠️  DATABASE_URL not found. Please set the environment variable:")
        print("   export DATABASE_URL='your_railway_postgres_url'")
        return None
    
    config_path = Path(__file__).parent / "configs" / "railway_test_config.yaml"
    config = TestConfig.from_file(str(config_path))
    
    # Override database URL from environment
    config.database_url = os.getenv("DATABASE_URL")
    
    test_runner = FACTTestRunner(config)
    
    try:
        await test_runner.initialize()
        summary = await test_runner.run_comprehensive_test()
        
        print(f"\n✅ Railway tests completed!")
        print(f"📊 Results: {summary.overall_metrics['success_rate']:.1%} success rate")
        print(f"⚡ Average response time: {summary.overall_metrics['avg_response_time_ms']:.1f}ms")
        print(f"📁 Results saved to: {config.output_dir}")
        
        # Check performance thresholds
        metrics = summary.overall_metrics
        if not metrics['performance_threshold_met']:
            print("⚠️  Performance thresholds not met:")
            for issue in metrics['performance_issues']:
                print(f"   - {issue}")
        
        return summary
        
    except Exception as e:
        print(f"\n❌ Railway tests failed: {e}")
        logger.error(f"Railway test error: {e}")
        raise
    finally:
        await test_runner.cleanup()


async def run_performance_tests():
    """Run high-load performance testing"""
    print("🏁 Running Performance Tests")
    print("=" * 50)
    
    config_path = Path(__file__).parent / "configs" / "performance_test_config.yaml"
    config = TestConfig.from_file(str(config_path))
    
    test_runner = FACTTestRunner(config)
    
    try:
        await test_runner.initialize()
        summary = await test_runner.run_comprehensive_test()
        
        print(f"\n🏆 Performance tests completed!")
        print(f"📊 Results: {summary.overall_metrics['success_rate']:.1%} success rate")
        print(f"⚡ Average response time: {summary.overall_metrics['avg_response_time_ms']:.1f}ms")
        print(f"🔥 Throughput: {config.test_question_count / summary.duration_seconds:.1f} req/s")
        print(f"📁 Results saved to: {config.output_dir}")
        
        return summary
        
    except Exception as e:
        print(f"\n❌ Performance tests failed: {e}")
        logger.error(f"Performance test error: {e}")
        raise
    finally:
        await test_runner.cleanup()


async def run_single_method_test(method: str, environment: str = "local"):
    """Run test for a single query method"""
    print(f"🎯 Running {method.upper()} Method Test ({environment})")
    print("=" * 50)
    
    config_path = Path(__file__).parent / "configs" / f"{environment}_test_config.yaml"
    config = TestConfig.from_file(str(config_path))
    
    # Override to test only specified method
    config.query_methods = [method]
    
    if environment == "railway":
        config.database_url = os.getenv("DATABASE_URL")
    
    test_runner = FACTTestRunner(config)
    
    try:
        await test_runner.initialize()
        
        method_enum = QueryMethod[method.upper()]
        summary = await test_runner.run_single_method_test(method_enum)
        
        print(f"\n✅ {method.upper()} method test completed!")
        print(f"📊 Success rate: {summary['success_rate']:.1%}")
        print(f"⚡ Average response time: {summary['avg_response_time_ms']:.1f}ms")
        print(f"🎯 Accuracy score: {summary['avg_accuracy']:.3f}")
        
        return summary
        
    except Exception as e:
        print(f"\n❌ {method.upper()} method test failed: {e}")
        logger.error(f"{method} method test error: {e}")
        raise
    finally:
        await test_runner.cleanup()


async def run_quick_validation():
    """Run quick validation test with minimal questions"""
    print("⚡ Running Quick Validation Test")
    print("=" * 50)
    
    config_path = Path(__file__).parent / "configs" / "local_test_config.yaml"
    config = TestConfig.from_file(str(config_path))
    
    # Override for quick test
    config.test_question_count = 20
    config.questions_per_batch = 10
    config.max_concurrent_tests = 5
    
    test_runner = FACTTestRunner(config)
    
    try:
        await test_runner.initialize()
        summary = await test_runner.run_comprehensive_test()
        
        print(f"\n⚡ Quick validation completed!")
        print(f"📊 Results: {summary.overall_metrics['success_rate']:.1%} success rate")
        print(f"⚡ Average response time: {summary.overall_metrics['avg_response_time_ms']:.1f}ms")
        
        # Quick health check
        if summary.overall_metrics['success_rate'] > 0.8:
            print("✅ System appears healthy")
        else:
            print("⚠️  System may have issues - run full tests for details")
        
        return summary
        
    except Exception as e:
        print(f"\n❌ Quick validation failed: {e}")
        logger.error(f"Quick validation error: {e}")
        raise
    finally:
        await test_runner.cleanup()


async def generate_sample_questions():
    """Generate and save sample test questions"""
    print("📝 Generating Sample Test Questions")
    print("=" * 50)
    
    from synthetic_questions import SyntheticQuestionGenerator
    
    generator = SyntheticQuestionGenerator()
    
    # Generate different sets
    test_sets = [
        ("comprehensive", 200, None),
        ("quick_test", 50, None),
        ("state_requirements_only", 100, ["state_licensing_requirements"]),
        ("exam_prep_only", 50, ["exam_preparation_testing"]),
    ]
    
    for set_name, count, categories in test_sets:
        questions = await generator.generate_questions(count=count, categories=categories)
        filename = f"test_results/{set_name}_questions.json"
        generator.export_questions(questions, filename)
        print(f"✅ Generated {len(questions)} questions for {set_name} -> {filename}")
    
    print("\n📁 All question sets generated successfully!")


def print_help():
    """Print detailed help information"""
    help_text = """
🧪 FACT System Automated Testing Framework

USAGE:
    python run_tests.py [command] [options]

COMMANDS:
    local           Run comprehensive local tests (200 questions)
    railway         Run production tests against Railway deployment  
    performance     Run high-load performance tests (500 questions)
    quick           Run quick validation test (20 questions)
    database        Test database query method only
    vapi            Test VAPI webhook method only
    api             Test REST API method only
    questions       Generate sample test questions
    help            Show this help message

EXAMPLES:
    # Run full local test suite
    python run_tests.py local
    
    # Test Railway production environment
    export DATABASE_URL="postgresql://..."
    python run_tests.py railway
    
    # Run performance benchmarking
    python run_tests.py performance
    
    # Quick health check
    python run_tests.py quick
    
    # Test specific method
    python run_tests.py database --env railway
    
    # Generate test questions
    python run_tests.py questions

CONFIGURATION:
    Test configurations are stored in tests/configs/:
    - local_test_config.yaml      (Local development)
    - railway_test_config.yaml    (Production testing)
    - performance_test_config.yaml (Performance testing)

OUTPUTS:
    Results are saved to test_results/ with timestamps:
    - Raw results JSON
    - Test summary JSON  
    - Human-readable report
    - Performance metrics

For more information, see the README.md file.
    """
    print(help_text)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="FACT System Test Runner")
    parser.add_argument("command", nargs="?", default="help", 
                       help="Test command to run")
    parser.add_argument("--env", choices=["local", "railway"], default="local",
                       help="Environment for single method tests")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Setup test environment
    setup_environment()
    
    # Route to appropriate test function
    try:
        if args.command == "local":
            await run_local_tests()
        elif args.command == "railway":
            await run_railway_tests()
        elif args.command == "performance":
            await run_performance_tests()
        elif args.command == "quick":
            await run_quick_validation()
        elif args.command == "database":
            await run_single_method_test("database", args.env)
        elif args.command == "vapi":
            await run_single_method_test("vapi", args.env)
        elif args.command == "api":
            await run_single_method_test("api", args.env)
        elif args.command == "questions":
            await generate_sample_questions()
        elif args.command == "help":
            print_help()
        else:
            print(f"❌ Unknown command: {args.command}")
            print("Use 'python run_tests.py help' for available commands")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
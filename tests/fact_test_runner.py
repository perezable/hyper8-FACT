"""
FACT System Automated Test Runner

Main test execution engine for comprehensive evaluation of the FACT system.
Supports multiple query methods, parallel execution, and detailed reporting.
"""

import asyncio
import json
import os
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import yaml
import concurrent.futures

from query_executor import QueryExecutor, QueryMethod, QueryResult
from response_collector import ResponseCollector, TestResult, TestSummary
from parallel_executor import ParallelExecutor
from synthetic_questions import SyntheticQuestionGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_runner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class TestConfig:
    """Test configuration settings"""
    # Environment settings
    environment: str = "local"  # local, railway
    database_url: Optional[str] = None
    api_base_url: Optional[str] = None
    vapi_webhook_url: Optional[str] = None
    
    # Test execution settings
    max_concurrent_tests: int = 10
    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Query settings
    query_methods: List[str] = None
    test_question_count: int = 200
    questions_per_batch: int = 50
    
    # Performance thresholds
    max_response_time_ms: float = 5000.0
    min_accuracy_threshold: float = 0.7
    max_error_rate: float = 0.1
    
    # Output settings
    output_dir: str = "test_results"
    detailed_logging: bool = True
    export_raw_data: bool = True
    
    def __post_init__(self):
        if self.query_methods is None:
            self.query_methods = ["database", "vapi", "api"]
    
    @classmethod
    def from_file(cls, config_path: str) -> 'TestConfig':
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


class FACTTestRunner:
    """
    Main test runner for FACT system evaluation.
    
    Orchestrates test execution across multiple query methods,
    manages parallel execution, and generates comprehensive reports.
    """
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.query_executor = QueryExecutor(config)
        self.response_collector = ResponseCollector(config)
        self.parallel_executor = ParallelExecutor(config)
        self.question_generator = SyntheticQuestionGenerator()
        
        # Create output directory
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Test session metadata
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = None
        self.end_time = None
        
    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing FACT Test Runner...")
        
        # Initialize query executor
        await self.query_executor.initialize()
        
        # Initialize response collector
        await self.response_collector.initialize()
        
        # Generate test questions
        await self._generate_test_questions()
        
        logger.info(f"Test runner initialized for session: {self.session_id}")
    
    async def _generate_test_questions(self):
        """Generate synthetic test questions"""
        logger.info(f"Generating {self.config.test_question_count} test questions...")
        
        self.test_questions = await self.question_generator.generate_questions(
            count=self.config.test_question_count,
            categories=[
                "state_licensing_requirements",
                "exam_preparation_testing", 
                "qualifier_network_programs",
                "business_formation_operations",
                "insurance_bonding",
                "financial_planning_roi",
                "success_stories_case_studies",
                "troubleshooting_problem_resolution"
            ]
        )
        
        # Save questions for review
        questions_file = self.output_dir / f"test_questions_{self.session_id}.json"
        with open(questions_file, 'w') as f:
            json.dump([q.to_dict() for q in self.test_questions], f, indent=2)
        
        logger.info(f"Generated {len(self.test_questions)} test questions")
    
    async def run_comprehensive_test(self) -> TestSummary:
        """
        Run comprehensive test across all configured query methods.
        
        Returns:
            TestSummary with complete results and metrics
        """
        self.start_time = datetime.now()
        logger.info(f"Starting comprehensive test at {self.start_time}")
        
        try:
            # Run tests for each query method
            all_results = []
            method_summaries = {}
            
            for method_name in self.config.query_methods:
                try:
                    method = QueryMethod[method_name.upper()]
                    logger.info(f"Testing query method: {method.value}")
                    
                    # Run test for this method
                    results = await self._run_method_test(method)
                    all_results.extend(results)
                    
                    # Collect method summary
                    method_summaries[method.value] = await self._summarize_method_results(results)
                    
                except Exception as e:
                    logger.error(f"Error testing method {method_name}: {e}")
                    method_summaries[method_name] = {
                        "error": str(e),
                        "total_tests": 0,
                        "success_count": 0,
                        "error_count": len(self.test_questions)
                    }
            
            # Generate comprehensive summary
            summary = await self._generate_comprehensive_summary(all_results, method_summaries)
            
            # Save results
            await self._save_results(all_results, summary)
            
            return summary
            
        except Exception as e:
            logger.error(f"Comprehensive test failed: {e}")
            raise
        finally:
            self.end_time = datetime.now()
            logger.info(f"Test completed at {self.end_time}")
    
    async def _run_method_test(self, method: QueryMethod) -> List[TestResult]:
        """Run test for a specific query method"""
        logger.info(f"Running {len(self.test_questions)} tests for method: {method.value}")
        
        # Create batches for parallel execution
        batches = [
            self.test_questions[i:i + self.config.questions_per_batch]
            for i in range(0, len(self.test_questions), self.config.questions_per_batch)
        ]
        
        all_results = []
        
        for batch_idx, batch in enumerate(batches):
            logger.info(f"Processing batch {batch_idx + 1}/{len(batches)} ({len(batch)} questions)")
            
            # Execute batch in parallel
            batch_results = await self.parallel_executor.execute_batch(
                method, batch, f"{method.value}_batch_{batch_idx}"
            )
            
            all_results.extend(batch_results)
            
            # Log progress
            success_count = sum(1 for r in batch_results if r.success)
            logger.info(f"Batch {batch_idx + 1} completed: {success_count}/{len(batch)} successful")
        
        logger.info(f"Method {method.value} completed: {len(all_results)} total results")
        return all_results
    
    async def _summarize_method_results(self, results: List[TestResult]) -> Dict[str, Any]:
        """Summarize results for a single method"""
        if not results:
            return {
                "total_tests": 0,
                "success_count": 0,
                "error_count": 0,
                "avg_response_time_ms": 0.0,
                "accuracy_score": 0.0
            }
        
        success_count = sum(1 for r in results if r.success)
        error_count = len(results) - success_count
        
        # Calculate average response time (only for successful requests)
        successful_results = [r for r in results if r.success and r.response_time_ms > 0]
        avg_response_time = (
            sum(r.response_time_ms for r in successful_results) / len(successful_results)
            if successful_results else 0.0
        )
        
        # Calculate accuracy score (placeholder - implement actual scoring)
        accuracy_scores = [r.accuracy_score for r in results if r.accuracy_score is not None]
        avg_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0.0
        
        return {
            "total_tests": len(results),
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": success_count / len(results),
            "error_rate": error_count / len(results),
            "avg_response_time_ms": avg_response_time,
            "accuracy_score": avg_accuracy,
            "performance_threshold_met": avg_response_time <= self.config.max_response_time_ms,
            "accuracy_threshold_met": avg_accuracy >= self.config.min_accuracy_threshold
        }
    
    async def _generate_comprehensive_summary(self, all_results: List[TestResult], 
                                            method_summaries: Dict[str, Any]) -> TestSummary:
        """Generate comprehensive test summary"""
        total_tests = len(all_results)
        successful_results = [r for r in all_results if r.success]
        
        overall_success_rate = len(successful_results) / total_tests if total_tests > 0 else 0.0
        overall_error_rate = 1 - overall_success_rate
        
        # Calculate overall performance metrics
        avg_response_time = (
            sum(r.response_time_ms for r in successful_results) / len(successful_results)
            if successful_results else 0.0
        )
        
        # Performance threshold analysis
        performance_issues = []
        if avg_response_time > self.config.max_response_time_ms:
            performance_issues.append(f"Average response time ({avg_response_time:.1f}ms) exceeds threshold ({self.config.max_response_time_ms}ms)")
        
        if overall_error_rate > self.config.max_error_rate:
            performance_issues.append(f"Error rate ({overall_error_rate:.2%}) exceeds threshold ({self.config.max_error_rate:.2%})")
        
        # Create summary
        summary = TestSummary(
            session_id=self.session_id,
            start_time=self.start_time,
            end_time=self.end_time,
            duration_seconds=(self.end_time - self.start_time).total_seconds(),
            config=self.config.to_dict(),
            method_summaries=method_summaries,
            overall_metrics={
                "total_tests": total_tests,
                "successful_tests": len(successful_results),
                "failed_tests": total_tests - len(successful_results),
                "success_rate": overall_success_rate,
                "error_rate": overall_error_rate,
                "avg_response_time_ms": avg_response_time,
                "performance_threshold_met": len(performance_issues) == 0,
                "performance_issues": performance_issues
            },
            all_results=all_results
        )
        
        return summary
    
    async def _save_results(self, all_results: List[TestResult], summary: TestSummary):
        """Save all test results and summary"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw results
        if self.config.export_raw_data:
            raw_results_file = self.output_dir / f"raw_results_{timestamp}.json"
            with open(raw_results_file, 'w') as f:
                json.dump([r.to_dict() for r in all_results], f, indent=2, default=str)
        
        # Save summary
        summary_file = self.output_dir / f"test_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary.to_dict(), f, indent=2, default=str)
        
        # Save human-readable report
        report_file = self.output_dir / f"test_report_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write(self._generate_text_report(summary))
        
        logger.info(f"Results saved to {self.output_dir}")
    
    def _generate_text_report(self, summary: TestSummary) -> str:
        """Generate human-readable test report"""
        report = []
        report.append("FACT System Automated Test Report")
        report.append("=" * 50)
        report.append(f"Session ID: {summary.session_id}")
        report.append(f"Test Duration: {summary.duration_seconds:.1f} seconds")
        report.append(f"Start Time: {summary.start_time}")
        report.append(f"End Time: {summary.end_time}")
        report.append("")
        
        # Overall metrics
        metrics = summary.overall_metrics
        report.append("OVERALL RESULTS")
        report.append("-" * 20)
        report.append(f"Total Tests: {metrics['total_tests']}")
        report.append(f"Successful: {metrics['successful_tests']} ({metrics['success_rate']:.1%})")
        report.append(f"Failed: {metrics['failed_tests']} ({metrics['error_rate']:.1%})")
        report.append(f"Average Response Time: {metrics['avg_response_time_ms']:.1f}ms")
        report.append(f"Performance Threshold Met: {metrics['performance_threshold_met']}")
        
        if metrics['performance_issues']:
            report.append("\nPerformance Issues:")
            for issue in metrics['performance_issues']:
                report.append(f"  - {issue}")
        
        # Method-specific results
        report.append("\nMETHOD-SPECIFIC RESULTS")
        report.append("-" * 30)
        
        for method, method_summary in summary.method_summaries.items():
            report.append(f"\n{method.upper()}:")
            if 'error' in method_summary:
                report.append(f"  ERROR: {method_summary['error']}")
            else:
                report.append(f"  Success Rate: {method_summary['success_rate']:.1%}")
                report.append(f"  Average Response Time: {method_summary['avg_response_time_ms']:.1f}ms")
                report.append(f"  Accuracy Score: {method_summary['accuracy_score']:.3f}")
                report.append(f"  Performance Threshold Met: {method_summary['performance_threshold_met']}")
                report.append(f"  Accuracy Threshold Met: {method_summary['accuracy_threshold_met']}")
        
        # Configuration
        report.append("\nTEST CONFIGURATION")
        report.append("-" * 20)
        report.append(f"Environment: {summary.config['environment']}")
        report.append(f"Query Methods: {', '.join(summary.config['query_methods'])}")
        report.append(f"Max Concurrent Tests: {summary.config['max_concurrent_tests']}")
        report.append(f"Request Timeout: {summary.config['request_timeout']}s")
        report.append(f"Max Retries: {summary.config['max_retries']}")
        
        return "\n".join(report)
    
    async def run_single_method_test(self, method: QueryMethod) -> Dict[str, Any]:
        """Run test for a single query method"""
        logger.info(f"Running single method test: {method.value}")
        
        results = await self._run_method_test(method)
        summary = await self._summarize_method_results(results)
        
        # Save method-specific results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        method_results_file = self.output_dir / f"{method.value}_results_{timestamp}.json"
        with open(method_results_file, 'w') as f:
            json.dump({
                "method": method.value,
                "summary": summary,
                "results": [r.to_dict() for r in results]
            }, f, indent=2, default=str)
        
        return summary
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.query_executor.cleanup()
            await self.response_collector.cleanup()
            logger.info("Test runner cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def create_default_config(environment: str = "local") -> TestConfig:
    """Create default test configuration"""
    if environment == "railway":
        return TestConfig(
            environment="railway",
            database_url=os.getenv("DATABASE_URL"),
            api_base_url="https://hyper8-fact-production.up.railway.app",
            vapi_webhook_url="https://hyper8-fact-production.up.railway.app/vapi/webhook",
            max_concurrent_tests=5,  # Lower for production
            request_timeout=45,
            test_question_count=100,  # Smaller test set for production
            questions_per_batch=25
        )
    else:
        return TestConfig(
            environment="local",
            database_url="sqlite:///data/fact_system.db",
            api_base_url="http://localhost:8000",
            vapi_webhook_url="http://localhost:8000/vapi/webhook",
            max_concurrent_tests=10,
            request_timeout=30,
            test_question_count=200,
            questions_per_batch=50
        )


async def main():
    """Main entry point for test runner"""
    parser = argparse.ArgumentParser(description="FACT System Test Runner")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--environment", choices=["local", "railway"], 
                       default="local", help="Test environment")
    parser.add_argument("--method", choices=["database", "vapi", "api"],
                       help="Single method to test")
    parser.add_argument("--output-dir", default="test_results",
                       help="Output directory for results")
    parser.add_argument("--questions", type=int, default=200,
                       help="Number of test questions")
    parser.add_argument("--concurrent", type=int, default=10,
                       help="Max concurrent tests")
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config:
        config = TestConfig.from_file(args.config)
    else:
        config = create_default_config(args.environment)
    
    # Override config with command line arguments
    if args.output_dir:
        config.output_dir = args.output_dir
    if args.questions:
        config.test_question_count = args.questions
    if args.concurrent:
        config.max_concurrent_tests = args.concurrent
    if args.method:
        config.query_methods = [args.method]
    
    # Create and run test
    test_runner = FACTTestRunner(config)
    
    try:
        await test_runner.initialize()
        
        if args.method:
            # Run single method test
            method = QueryMethod[args.method.upper()]
            summary = await test_runner.run_single_method_test(method)
            print(f"\nTest completed for method: {method.value}")
            print(f"Success Rate: {summary['success_rate']:.1%}")
            print(f"Average Response Time: {summary['avg_response_time_ms']:.1f}ms")
        else:
            # Run comprehensive test
            summary = await test_runner.run_comprehensive_test()
            print(f"\nComprehensive test completed")
            print(f"Overall Success Rate: {summary.overall_metrics['success_rate']:.1%}")
            print(f"Average Response Time: {summary.overall_metrics['avg_response_time_ms']:.1f}ms")
        
        print(f"Results saved to: {config.output_dir}")
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    finally:
        await test_runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
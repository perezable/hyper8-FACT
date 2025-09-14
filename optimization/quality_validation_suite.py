"""
Comprehensive Quality Validation Suite for FACT System

Automated testing framework for response accuracy, A/B testing,
continuous improvement metrics, and quality assurance workflows.
"""

import asyncio
import json
import time
import hashlib
import random
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from datetime import datetime, timedelta
import structlog
from pathlib import Path
import statistics

logger = structlog.get_logger(__name__)


@dataclass
class ValidationTest:
    """Individual validation test case."""
    test_id: str
    test_type: str  # 'accuracy', 'performance', 'consistency', 'coverage'
    category: str
    query: str
    expected_keywords: List[str]
    expected_min_confidence: float
    expected_max_response_time_ms: float
    state_context: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of a validation test."""
    test_id: str
    test_type: str
    passed: bool
    actual_response: str
    confidence_score: float
    response_time_ms: float
    keyword_matches: List[str]
    missing_keywords: List[str]
    issues_found: List[str]
    improvements_suggested: List[str]
    timestamp: float = field(default_factory=time.time)


@dataclass
class ABTestConfig:
    """A/B test configuration."""
    test_name: str
    test_type: str  # 'algorithm', 'prompt', 'cache_strategy'
    variant_a: Dict[str, Any]
    variant_b: Dict[str, Any]
    success_metric: str  # 'accuracy', 'response_time', 'confidence'
    minimum_samples: int = 100
    confidence_level: float = 0.95
    duration_hours: int = 24


@dataclass
class ABTestResult:
    """A/B test results with statistical significance."""
    test_name: str
    start_time: float
    end_time: float
    variant_a_samples: int
    variant_b_samples: int
    variant_a_metric: float
    variant_b_metric: float
    improvement_percent: float
    statistical_significance: bool
    p_value: float
    confidence_interval: Tuple[float, float]
    recommendation: str


class QualityValidationSuite:
    """
    Comprehensive quality validation and testing framework.
    
    Provides automated testing, A/B testing capabilities, and continuous
    improvement metrics for the FACT system.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize quality validation suite."""
        self.config = config or self._get_default_config()
        self.test_cases = self._load_test_cases()
        self.validation_history: List[ValidationResult] = []
        self.ab_tests: Dict[str, ABTestConfig] = {}
        self.ab_test_results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        logger.info("Quality validation suite initialized",
                   test_cases_loaded=len(self.test_cases))
    
    async def run_full_validation(self) -> Dict[str, Any]:
        """Run complete validation suite across all test categories."""
        logger.info("Starting full validation suite")
        start_time = time.time()
        
        results = {
            'accuracy_tests': await self._run_accuracy_tests(),
            'performance_tests': await self._run_performance_tests(),
            'consistency_tests': await self._run_consistency_tests(),
            'coverage_tests': await self._run_coverage_tests(),
            'regression_tests': await self._run_regression_tests()
        }
        
        # Generate summary
        summary = self._generate_validation_summary(results)
        execution_time = time.time() - start_time
        
        logger.info("Full validation completed",
                   execution_time_seconds=execution_time,
                   overall_pass_rate=summary['overall_pass_rate'])
        
        return {
            'execution_time_seconds': execution_time,
            'timestamp': time.time(),
            'results': results,
            'summary': summary,
            'recommendations': self._generate_quality_recommendations(results)
        }
    
    async def _run_accuracy_tests(self) -> List[ValidationResult]:
        """Run accuracy validation tests."""
        logger.info("Running accuracy tests")
        accuracy_tests = [t for t in self.test_cases if t.test_type == 'accuracy']
        results = []
        
        for test in accuracy_tests:
            try:
                # Simulate query execution (replace with actual FACT system call)
                response, confidence, response_time = await self._execute_test_query(test)
                
                # Validate response accuracy
                keyword_matches = self._check_keyword_matches(response, test.expected_keywords)
                missing_keywords = [kw for kw in test.expected_keywords if kw not in keyword_matches]
                
                # Determine pass/fail
                passed = (
                    len(missing_keywords) == 0 and
                    confidence >= test.expected_min_confidence and
                    response_time <= test.expected_max_response_time_ms
                )
                
                # Identify issues
                issues = []
                if missing_keywords:
                    issues.append(f"Missing keywords: {missing_keywords}")
                if confidence < test.expected_min_confidence:
                    issues.append(f"Low confidence: {confidence:.2f} < {test.expected_min_confidence}")
                if response_time > test.expected_max_response_time_ms:
                    issues.append(f"Slow response: {response_time:.1f}ms > {test.expected_max_response_time_ms}ms")
                
                # Generate improvement suggestions
                improvements = self._generate_test_improvements(test, response, confidence, response_time)
                
                result = ValidationResult(
                    test_id=test.test_id,
                    test_type=test.test_type,
                    passed=passed,
                    actual_response=response,
                    confidence_score=confidence,
                    response_time_ms=response_time,
                    keyword_matches=keyword_matches,
                    missing_keywords=missing_keywords,
                    issues_found=issues,
                    improvements_suggested=improvements
                )
                
                results.append(result)
                self.validation_history.append(result)
                
            except Exception as e:
                logger.error("Accuracy test failed", test_id=test.test_id, error=str(e))
                # Record failed test
                result = ValidationResult(
                    test_id=test.test_id,
                    test_type=test.test_type,
                    passed=False,
                    actual_response="",
                    confidence_score=0.0,
                    response_time_ms=0.0,
                    keyword_matches=[],
                    missing_keywords=test.expected_keywords,
                    issues_found=[f"Test execution failed: {str(e)}"],
                    improvements_suggested=["Fix test execution infrastructure"]
                )
                results.append(result)
        
        logger.info("Accuracy tests completed",
                   total_tests=len(accuracy_tests),
                   passed_tests=sum(1 for r in results if r.passed))
        
        return results
    
    async def _run_performance_tests(self) -> List[ValidationResult]:
        """Run performance validation tests."""
        logger.info("Running performance tests")
        performance_tests = [t for t in self.test_cases if t.test_type == 'performance']
        results = []
        
        for test in performance_tests:
            try:
                # Run test multiple times for statistical significance
                response_times = []
                confidences = []
                
                for _ in range(5):  # 5 iterations per test
                    response, confidence, response_time = await self._execute_test_query(test)
                    response_times.append(response_time)
                    confidences.append(confidence)
                
                avg_response_time = statistics.mean(response_times)
                avg_confidence = statistics.mean(confidences)
                p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)
                
                # Performance criteria
                passed = (
                    avg_response_time <= test.expected_max_response_time_ms and
                    p95_response_time <= test.expected_max_response_time_ms * 1.5 and
                    avg_confidence >= test.expected_min_confidence
                )
                
                # Identify performance issues
                issues = []
                if avg_response_time > test.expected_max_response_time_ms:
                    issues.append(f"Average response time exceeds target: {avg_response_time:.1f}ms > {test.expected_max_response_time_ms}ms")
                if p95_response_time > test.expected_max_response_time_ms * 1.5:
                    issues.append(f"P95 response time too high: {p95_response_time:.1f}ms")
                
                result = ValidationResult(
                    test_id=test.test_id,
                    test_type=test.test_type,
                    passed=passed,
                    actual_response=response,
                    confidence_score=avg_confidence,
                    response_time_ms=avg_response_time,
                    keyword_matches=[],
                    missing_keywords=[],
                    issues_found=issues,
                    improvements_suggested=self._generate_performance_improvements(avg_response_time, test.expected_max_response_time_ms)
                )
                
                results.append(result)
                
            except Exception as e:
                logger.error("Performance test failed", test_id=test.test_id, error=str(e))
        
        return results
    
    async def _run_consistency_tests(self) -> List[ValidationResult]:
        """Run consistency validation tests."""
        logger.info("Running consistency tests")
        consistency_tests = [t for t in self.test_cases if t.test_type == 'consistency']
        results = []
        
        for test in consistency_tests:
            try:
                # Run same query multiple times to check consistency
                responses = []
                confidences = []
                response_times = []
                
                for _ in range(3):  # 3 iterations for consistency check
                    response, confidence, response_time = await self._execute_test_query(test)
                    responses.append(response)
                    confidences.append(confidence)
                    response_times.append(response_time)
                
                # Analyze consistency
                confidence_variance = statistics.variance(confidences) if len(confidences) > 1 else 0
                response_time_variance = statistics.variance(response_times) if len(response_times) > 1 else 0
                
                # Check response similarity
                response_similarity = self._calculate_response_similarity(responses)
                
                # Consistency criteria
                passed = (
                    confidence_variance < 0.05 and  # Low confidence variance
                    response_time_variance < (statistics.mean(response_times) * 0.2) ** 2 and  # Low time variance
                    response_similarity > 0.8  # High response similarity
                )
                
                issues = []
                if confidence_variance >= 0.05:
                    issues.append(f"High confidence variance: {confidence_variance:.3f}")
                if response_similarity <= 0.8:
                    issues.append(f"Low response similarity: {response_similarity:.3f}")
                
                result = ValidationResult(
                    test_id=test.test_id,
                    test_type=test.test_type,
                    passed=passed,
                    actual_response=responses[0],  # Use first response as representative
                    confidence_score=statistics.mean(confidences),
                    response_time_ms=statistics.mean(response_times),
                    keyword_matches=[],
                    missing_keywords=[],
                    issues_found=issues,
                    improvements_suggested=self._generate_consistency_improvements(confidence_variance, response_similarity)
                )
                
                results.append(result)
                
            except Exception as e:
                logger.error("Consistency test failed", test_id=test.test_id, error=str(e))
        
        return results
    
    async def _run_coverage_tests(self) -> List[ValidationResult]:
        """Run coverage validation tests."""
        logger.info("Running coverage tests")
        coverage_tests = [t for t in self.test_cases if t.test_type == 'coverage']
        results = []
        
        # Test coverage across different categories and states
        categories_tested = set()
        states_tested = set()
        
        for test in coverage_tests:
            try:
                response, confidence, response_time = await self._execute_test_query(test)
                
                # Track coverage
                categories_tested.add(test.category)
                if test.state_context:
                    states_tested.add(test.state_context)
                
                # Coverage criteria (broader than accuracy tests)
                passed = (
                    len(response.strip()) > 50 and  # Substantial response
                    confidence >= 0.5 and  # Minimum confidence threshold
                    response_time <= test.expected_max_response_time_ms * 2  # More lenient timing
                )
                
                keyword_matches = self._check_keyword_matches(response, test.expected_keywords)
                
                result = ValidationResult(
                    test_id=test.test_id,
                    test_type=test.test_type,
                    passed=passed,
                    actual_response=response,
                    confidence_score=confidence,
                    response_time_ms=response_time,
                    keyword_matches=keyword_matches,
                    missing_keywords=[kw for kw in test.expected_keywords if kw not in keyword_matches],
                    issues_found=[],
                    improvements_suggested=[]
                )
                
                results.append(result)
                
            except Exception as e:
                logger.error("Coverage test failed", test_id=test.test_id, error=str(e))
        
        # Analyze coverage gaps
        expected_categories = {'state_licensing_requirements', 'exam_preparation_testing', 'business_operations_finance', 'troubleshooting_problems'}
        expected_states = {'GA', 'CA', 'FL', 'TX', 'NY'}
        
        missing_categories = expected_categories - categories_tested
        missing_states = expected_states - states_tested
        
        if missing_categories or missing_states:
            logger.warning("Coverage gaps identified",
                          missing_categories=list(missing_categories),
                          missing_states=list(missing_states))
        
        return results
    
    async def _run_regression_tests(self) -> List[ValidationResult]:
        """Run regression tests against previous validation results."""
        logger.info("Running regression tests")
        
        if not self.validation_history:
            logger.info("No validation history for regression testing")
            return []
        
        # Get previous results for comparison
        cutoff_time = time.time() - (7 * 24 * 3600)  # Last 7 days
        previous_results = [r for r in self.validation_history if r.timestamp >= cutoff_time]
        
        if not previous_results:
            return []
        
        # Calculate previous performance baseline
        previous_accuracy = sum(1 for r in previous_results if r.passed and r.test_type == 'accuracy') / max(1, sum(1 for r in previous_results if r.test_type == 'accuracy'))
        previous_avg_response_time = statistics.mean([r.response_time_ms for r in previous_results if r.test_type == 'performance'])
        previous_avg_confidence = statistics.mean([r.confidence_score for r in previous_results])
        
        # Run current tests and compare
        current_accuracy_tests = await self._run_accuracy_tests()
        current_performance_tests = await self._run_performance_tests()
        
        current_accuracy = sum(1 for r in current_accuracy_tests if r.passed) / max(1, len(current_accuracy_tests))
        current_avg_response_time = statistics.mean([r.response_time_ms for r in current_performance_tests])
        current_avg_confidence = statistics.mean([r.confidence_score for r in current_accuracy_tests + current_performance_tests])
        
        # Create regression test result
        regression_passed = (
            current_accuracy >= previous_accuracy * 0.95 and  # Allow 5% degradation
            current_avg_response_time <= previous_avg_response_time * 1.1 and  # Allow 10% slowdown
            current_avg_confidence >= previous_avg_confidence * 0.95  # Allow 5% confidence drop
        )
        
        issues = []
        if current_accuracy < previous_accuracy * 0.95:
            issues.append(f"Accuracy regression: {current_accuracy:.1%} vs {previous_accuracy:.1%}")
        if current_avg_response_time > previous_avg_response_time * 1.1:
            issues.append(f"Performance regression: {current_avg_response_time:.1f}ms vs {previous_avg_response_time:.1f}ms")
        if current_avg_confidence < previous_avg_confidence * 0.95:
            issues.append(f"Confidence regression: {current_avg_confidence:.2f} vs {previous_avg_confidence:.2f}")
        
        regression_result = ValidationResult(
            test_id="regression_test_001",
            test_type="regression",
            passed=regression_passed,
            actual_response=f"Current vs Previous: Accuracy {current_accuracy:.1%} vs {previous_accuracy:.1%}",
            confidence_score=current_avg_confidence,
            response_time_ms=current_avg_response_time,
            keyword_matches=[],
            missing_keywords=[],
            issues_found=issues,
            improvements_suggested=self._generate_regression_improvements(issues)
        )
        
        return [regression_result]
    
    def setup_ab_test(self, config: ABTestConfig):
        """Set up a new A/B test."""
        self.ab_tests[config.test_name] = config
        self.ab_test_results[config.test_name] = []
        logger.info("A/B test configured", test_name=config.test_name, test_type=config.test_type)
    
    def record_ab_test_result(self, test_name: str, variant: str, metric_value: float, metadata: Optional[Dict[str, Any]] = None):
        """Record a result for an active A/B test."""
        if test_name not in self.ab_tests:
            logger.warning("Unknown A/B test", test_name=test_name)
            return
        
        result = {
            'timestamp': time.time(),
            'variant': variant,
            'metric_value': metric_value,
            'metadata': metadata or {}
        }
        
        self.ab_test_results[test_name].append(result)
    
    def analyze_ab_test(self, test_name: str) -> Optional[ABTestResult]:
        """Analyze A/B test results for statistical significance."""
        if test_name not in self.ab_tests:
            return None
        
        config = self.ab_tests[test_name]
        results = self.ab_test_results[test_name]
        
        # Separate results by variant
        variant_a_results = [r for r in results if r['variant'] == 'A']
        variant_b_results = [r for r in results if r['variant'] == 'B']
        
        if len(variant_a_results) < config.minimum_samples or len(variant_b_results) < config.minimum_samples:
            logger.info("Insufficient samples for A/B test analysis",
                       test_name=test_name,
                       variant_a_samples=len(variant_a_results),
                       variant_b_samples=len(variant_b_results),
                       required_samples=config.minimum_samples)
            return None
        
        # Calculate metrics
        variant_a_metric = statistics.mean([r['metric_value'] for r in variant_a_results])
        variant_b_metric = statistics.mean([r['metric_value'] for r in variant_b_results])
        
        # Calculate improvement
        if variant_a_metric != 0:
            improvement_percent = ((variant_b_metric - variant_a_metric) / variant_a_metric) * 100
        else:
            improvement_percent = 0.0
        
        # Simple statistical significance test (t-test approximation)
        # In production, use proper statistical testing libraries
        statistical_significance = abs(improvement_percent) > 5.0 and len(variant_a_results) > 30
        p_value = 0.05 if statistical_significance else 0.15  # Simplified
        
        # Generate recommendation
        if statistical_significance:
            if improvement_percent > 0:
                recommendation = f"Variant B shows {improvement_percent:.1f}% improvement. Recommend implementing Variant B."
            else:
                recommendation = f"Variant A performs {abs(improvement_percent):.1f}% better. Recommend keeping Variant A."
        else:
            recommendation = "No statistically significant difference. Continue testing or implement based on other factors."
        
        return ABTestResult(
            test_name=test_name,
            start_time=min(r['timestamp'] for r in results),
            end_time=max(r['timestamp'] for r in results),
            variant_a_samples=len(variant_a_results),
            variant_b_samples=len(variant_b_results),
            variant_a_metric=variant_a_metric,
            variant_b_metric=variant_b_metric,
            improvement_percent=improvement_percent,
            statistical_significance=statistical_significance,
            p_value=p_value,
            confidence_interval=(improvement_percent - 2, improvement_percent + 2),  # Simplified
            recommendation=recommendation
        )
    
    def generate_quality_report(self) -> Dict[str, Any]:
        """Generate comprehensive quality report."""
        if not self.validation_history:
            return {"error": "No validation history available"}
        
        # Recent results (last 24 hours)
        cutoff_time = time.time() - (24 * 3600)
        recent_results = [r for r in self.validation_history if r.timestamp >= cutoff_time]
        
        if not recent_results:
            recent_results = self.validation_history[-10:]  # Last 10 results
        
        # Calculate quality metrics
        overall_pass_rate = sum(1 for r in recent_results if r.passed) / len(recent_results)
        avg_confidence = statistics.mean([r.confidence_score for r in recent_results])
        avg_response_time = statistics.mean([r.response_time_ms for r in recent_results])
        
        # Quality trends
        test_type_performance = {}
        for test_type in ['accuracy', 'performance', 'consistency', 'coverage']:
            type_results = [r for r in recent_results if r.test_type == test_type]
            if type_results:
                test_type_performance[test_type] = {
                    'pass_rate': sum(1 for r in type_results if r.passed) / len(type_results),
                    'avg_confidence': statistics.mean([r.confidence_score for r in type_results]),
                    'avg_response_time': statistics.mean([r.response_time_ms for r in type_results])
                }
        
        # A/B test summaries
        ab_test_summaries = {}
        for test_name in self.ab_tests:
            ab_result = self.analyze_ab_test(test_name)
            if ab_result:
                ab_test_summaries[test_name] = asdict(ab_result)
        
        return {
            'report_timestamp': time.time(),
            'analysis_period_hours': 24,
            'total_tests_analyzed': len(recent_results),
            
            'overall_metrics': {
                'pass_rate': overall_pass_rate,
                'avg_confidence_score': avg_confidence,
                'avg_response_time_ms': avg_response_time,
                'quality_score': self._calculate_quality_score(recent_results)
            },
            
            'test_type_performance': test_type_performance,
            
            'ab_test_results': ab_test_summaries,
            
            'quality_trends': self._analyze_quality_trends(),
            
            'top_issues': self._identify_top_issues(recent_results),
            
            'improvement_opportunities': self._identify_improvement_opportunities(recent_results),
            
            'recommendations': self._generate_quality_recommendations({'recent_results': recent_results})
        }
    
    def export_validation_results(self, filepath: Optional[str] = None) -> str:
        """Export validation results to JSON file."""
        if not filepath:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"optimization/validation_results_{timestamp}.json"
        
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            export_data = {
                "export_timestamp": time.time(),
                "validation_history": [asdict(r) for r in self.validation_history],
                "test_cases": [asdict(t) for t in self.test_cases],
                "ab_tests": {name: asdict(config) for name, config in self.ab_tests.items()},
                "ab_test_results": dict(self.ab_test_results),
                "quality_report": self.generate_quality_report()
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info("Validation results exported", filepath=filepath)
            return filepath
        
        except Exception as e:
            logger.error("Failed to export validation results", error=str(e))
            raise
    
    async def _execute_test_query(self, test: ValidationTest) -> Tuple[str, float, float]:
        """Execute a test query and return response, confidence, and time."""
        # This is a placeholder - replace with actual FACT system integration
        start_time = time.time()
        
        # Simulate query processing
        await asyncio.sleep(random.uniform(0.05, 0.3))  # Simulate processing time
        
        response_time_ms = (time.time() - start_time) * 1000
        
        # Simulate response based on test expectations
        if test.test_type == 'accuracy':
            confidence = random.uniform(0.7, 0.95)
            response = f"Response for {test.query} containing {', '.join(test.expected_keywords[:2])}"
        elif test.test_type == 'performance':
            confidence = random.uniform(0.6, 0.9)
            response = f"Performance test response for {test.query}"
            # Simulate performance variation
            response_time_ms = random.uniform(50, 250)
        else:
            confidence = random.uniform(0.5, 0.8)
            response = f"Test response for {test.query}"
        
        return response, confidence, response_time_ms
    
    def _check_keyword_matches(self, response: str, expected_keywords: List[str]) -> List[str]:
        """Check which expected keywords are present in the response."""
        response_lower = response.lower()
        return [kw for kw in expected_keywords if kw.lower() in response_lower]
    
    def _calculate_response_similarity(self, responses: List[str]) -> float:
        """Calculate similarity between multiple responses."""
        if len(responses) < 2:
            return 1.0
        
        # Simple similarity based on shared words
        word_sets = [set(response.lower().split()) for response in responses]
        
        total_similarity = 0
        comparisons = 0
        
        for i in range(len(word_sets)):
            for j in range(i + 1, len(word_sets)):
                intersection = len(word_sets[i] & word_sets[j])
                union = len(word_sets[i] | word_sets[j])
                similarity = intersection / union if union > 0 else 0
                total_similarity += similarity
                comparisons += 1
        
        return total_similarity / comparisons if comparisons > 0 else 1.0
    
    def _generate_validation_summary(self, results: Dict[str, List[ValidationResult]]) -> Dict[str, Any]:
        """Generate summary of validation results."""
        all_results = []
        for test_results in results.values():
            all_results.extend(test_results)
        
        if not all_results:
            return {}
        
        return {
            'total_tests': len(all_results),
            'passed_tests': sum(1 for r in all_results if r.passed),
            'failed_tests': sum(1 for r in all_results if not r.passed),
            'overall_pass_rate': sum(1 for r in all_results if r.passed) / len(all_results),
            'avg_confidence': statistics.mean([r.confidence_score for r in all_results]),
            'avg_response_time': statistics.mean([r.response_time_ms for r in all_results]),
            'test_type_breakdown': {
                test_type: {
                    'total': len(test_results),
                    'passed': sum(1 for r in test_results if r.passed),
                    'pass_rate': sum(1 for r in test_results if r.passed) / len(test_results) if test_results else 0
                }
                for test_type, test_results in results.items()
            }
        }
    
    def _calculate_quality_score(self, results: List[ValidationResult]) -> float:
        """Calculate overall quality score (0-100)."""
        if not results:
            return 0.0
        
        pass_rate = sum(1 for r in results if r.passed) / len(results)
        avg_confidence = statistics.mean([r.confidence_score for r in results])
        avg_response_time = statistics.mean([r.response_time_ms for r in results])
        
        # Normalize response time score (lower is better)
        response_time_score = max(0, (300 - avg_response_time) / 300)
        
        # Weighted quality score
        quality_score = (
            pass_rate * 0.4 +
            avg_confidence * 0.3 +
            response_time_score * 0.3
        ) * 100
        
        return round(quality_score, 1)
    
    def _load_test_cases(self) -> List[ValidationTest]:
        """Load validation test cases."""
        return [
            ValidationTest(
                test_id="accuracy_001",
                test_type="accuracy",
                category="state_licensing_requirements",
                query="Georgia contractor license requirements",
                expected_keywords=["georgia", "license", "requirements", "contractor", "$2,500"],
                expected_min_confidence=0.8,
                expected_max_response_time_ms=150,
                state_context="GA"
            ),
            ValidationTest(
                test_id="accuracy_002",
                test_type="accuracy",
                category="exam_preparation_testing",
                query="PSI exam information",
                expected_keywords=["psi", "exam", "testing", "computer-based", "appointment"],
                expected_min_confidence=0.75,
                expected_max_response_time_ms=120,
            ),
            ValidationTest(
                test_id="performance_001",
                test_type="performance",
                category="state_licensing_requirements",
                query="California contractor license costs",
                expected_keywords=["california", "cost", "fee"],
                expected_min_confidence=0.7,
                expected_max_response_time_ms=100,
                state_context="CA"
            ),
            # Add more test cases as needed
        ]
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default validation configuration."""
        return {
            "accuracy_threshold": 0.8,
            "performance_threshold_ms": 150,
            "consistency_threshold": 0.8,
            "coverage_threshold": 0.7,
            "minimum_ab_test_samples": 100,
            "statistical_confidence_level": 0.95
        }
    
    def _generate_test_improvements(self, test: ValidationTest, response: str, confidence: float, response_time: float) -> List[str]:
        """Generate improvement suggestions for a specific test."""
        improvements = []
        
        if confidence < test.expected_min_confidence:
            improvements.append("Improve answer specificity and detail in knowledge base")
            improvements.append("Add more comprehensive examples and explanations")
        
        if response_time > test.expected_max_response_time_ms:
            improvements.append("Optimize database queries for this query pattern")
            improvements.append("Consider caching this type of response")
        
        return improvements
    
    def _generate_performance_improvements(self, actual_time: float, target_time: float) -> List[str]:
        """Generate performance improvement suggestions."""
        if actual_time <= target_time:
            return []
        
        return [
            "Add database indexes for common query patterns",
            "Implement result caching for frequent queries",
            "Optimize search algorithm parameters",
            "Consider query preprocessing"
        ]
    
    def _generate_consistency_improvements(self, confidence_variance: float, response_similarity: float) -> List[str]:
        """Generate consistency improvement suggestions."""
        improvements = []
        
        if confidence_variance >= 0.05:
            improvements.append("Improve search algorithm determinism")
            improvements.append("Review confidence scoring mechanism")
        
        if response_similarity <= 0.8:
            improvements.append("Standardize response templates")
            improvements.append("Improve result ranking consistency")
        
        return improvements
    
    def _generate_regression_improvements(self, issues: List[str]) -> List[str]:
        """Generate regression improvement suggestions."""
        if not issues:
            return []
        
        return [
            "Review recent system changes for performance impact",
            "Restore previous configuration if degradation is significant",
            "Implement additional monitoring and alerting",
            "Consider A/B testing for system changes"
        ]
    
    def _analyze_quality_trends(self) -> Dict[str, Any]:
        """Analyze quality trends over time."""
        if len(self.validation_history) < 10:
            return {"insufficient_data": True}
        
        # Get recent results for trend analysis
        recent_results = self.validation_history[-20:]  # Last 20 results
        first_half = recent_results[:10]
        second_half = recent_results[10:]
        
        def calculate_trend(results_a, results_b, metric):
            if not results_a or not results_b:
                return 0.0
            
            avg_a = statistics.mean([getattr(r, metric) for r in results_a])
            avg_b = statistics.mean([getattr(r, metric) for r in results_b])
            
            if avg_a == 0:
                return 0.0
            
            return ((avg_b - avg_a) / avg_a) * 100
        
        return {
            "confidence_trend_percent": calculate_trend(first_half, second_half, 'confidence_score'),
            "response_time_trend_percent": calculate_trend(first_half, second_half, 'response_time_ms'),
            "pass_rate_trend_percent": (
                (sum(1 for r in second_half if r.passed) / len(second_half)) -
                (sum(1 for r in first_half if r.passed) / len(first_half))
            ) * 100
        }
    
    def _identify_top_issues(self, results: List[ValidationResult]) -> List[Dict[str, Any]]:
        """Identify top quality issues."""
        issue_counts = defaultdict(int)
        
        for result in results:
            for issue in result.issues_found:
                issue_counts[issue] += 1
        
        top_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return [
            {"issue": issue, "occurrence_count": count, "impact": "high" if count > len(results) * 0.2 else "medium"}
            for issue, count in top_issues
        ]
    
    def _identify_improvement_opportunities(self, results: List[ValidationResult]) -> List[str]:
        """Identify improvement opportunities."""
        improvements = defaultdict(int)
        
        for result in results:
            for improvement in result.improvements_suggested:
                improvements[improvement] += 1
        
        return [improvement for improvement, count in improvements.items() if count >= 2]
    
    def _generate_quality_recommendations(self, validation_data: Dict[str, Any]) -> List[str]:
        """Generate quality improvement recommendations."""
        recommendations = []
        
        if 'recent_results' in validation_data:
            results = validation_data['recent_results']
            pass_rate = sum(1 for r in results if r.passed) / len(results) if results else 0
            
            if pass_rate < 0.8:
                recommendations.append("Improve knowledge base content coverage and accuracy")
            
            if results:
                avg_confidence = statistics.mean([r.confidence_score for r in results])
                if avg_confidence < 0.7:
                    recommendations.append("Enhance answer quality and specificity")
                
                avg_response_time = statistics.mean([r.response_time_ms for r in results])
                if avg_response_time > 150:
                    recommendations.append("Optimize system performance and response times")
        
        return recommendations


if __name__ == "__main__":
    # Example usage
    async def main():
        suite = QualityValidationSuite()
        
        # Run full validation
        results = await suite.run_full_validation()
        
        print("Validation Results:")
        print(f"Overall pass rate: {results['summary']['overall_pass_rate']:.1%}")
        print(f"Average confidence: {results['summary']['avg_confidence']:.2f}")
        print(f"Average response time: {results['summary']['avg_response_time']:.1f}ms")
        
        # Generate quality report
        report = suite.generate_quality_report()
        print(f"Quality score: {report['overall_metrics']['quality_score']}/100")
        
        # Export results
        filepath = suite.export_validation_results()
        print(f"Results exported to: {filepath}")
    
    asyncio.run(main())
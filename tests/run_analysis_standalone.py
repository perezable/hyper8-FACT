#!/usr/bin/env python3
"""
FACT System - Standalone Performance Analysis Demo

This script runs the comprehensive performance analysis pipeline in standalone mode
without requiring database connections, using simulated test data.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import structlog
import random
import numpy as np

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

logger = structlog.get_logger(__name__)


def generate_comprehensive_test_data(num_responses: int = 200) -> List[Dict[str, Any]]:
    """Generate comprehensive test data with realistic patterns."""
    
    personas = ['insurance_agent', 'insurance_broker', 'claims_adjuster', 'underwriter', 'producer']
    categories = ['licensing', 'continuing_education', 'renewals', 'exams', 'regulations', 'compliance', 'ethics']
    states = ['CA', 'TX', 'FL', 'NY', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI', 'AZ', 'WA', 'CO', 'NJ', 'MA']
    difficulties = ['easy', 'medium', 'hard']
    match_types = ['exact', 'fuzzy', 'keyword', 'partial', 'none']
    
    # Sample question templates
    question_templates = [
        "{state} insurance agent licensing requirements",
        "How many CE hours needed in {state}?",
        "What is the fee for {category} license in {state}?",
        "When does my {category} license expire in {state}?",
        "What are the {category} requirements for {state}?",
        "How do I renew my license in {state}?",
        "What exams are required for {category} in {state}?",
        "Ethics requirements for {category} in {state}",
        "License reinstatement process for {state}",
        "How to transfer license from {state} to another state?"
    ]
    
    sample_data = []
    
    for i in range(num_responses):
        persona = random.choice(personas)
        category = random.choice(categories)
        state = random.choice(states)
        difficulty = random.choice(difficulties)
        
        # Generate question variation
        template = random.choice(question_templates)
        original_question = template.format(state=state, category=category)
        query_variation = original_question.lower().replace('?', '') + "?"
        
        # Generate performance characteristics with realistic patterns
        
        # Base performance by category
        category_performance = {
            'licensing': {'confidence': 0.85, 'score': 0.82, 'response_time': 180},
            'continuing_education': {'confidence': 0.78, 'score': 0.75, 'response_time': 220},
            'renewals': {'confidence': 0.80, 'score': 0.77, 'response_time': 200},
            'exams': {'confidence': 0.72, 'score': 0.68, 'response_time': 280},
            'regulations': {'confidence': 0.65, 'score': 0.60, 'response_time': 350},
            'compliance': {'confidence': 0.68, 'score': 0.63, 'response_time': 320},
            'ethics': {'confidence': 0.75, 'score': 0.70, 'response_time': 240}
        }
        
        # Difficulty modifiers
        difficulty_modifiers = {
            'easy': {'confidence': 1.15, 'score': 1.20, 'response_time': 0.8},
            'medium': {'confidence': 1.0, 'score': 1.0, 'response_time': 1.0},
            'hard': {'confidence': 0.75, 'score': 0.70, 'response_time': 1.4}
        }
        
        # State coverage variations (some states have better coverage)
        state_coverage = {
            'CA': 0.95, 'TX': 0.92, 'FL': 0.88, 'NY': 0.90, 'IL': 0.85,
            'PA': 0.82, 'OH': 0.80, 'GA': 0.78, 'NC': 0.75, 'MI': 0.77,
            'AZ': 0.70, 'WA': 0.68, 'CO': 0.65, 'NJ': 0.72, 'MA': 0.74
        }
        
        # Get base metrics
        base_metrics = category_performance[category]
        difficulty_mod = difficulty_modifiers[difficulty]
        state_mod = state_coverage[state]
        
        # Calculate adjusted metrics
        base_confidence = base_metrics['confidence'] * difficulty_mod['confidence'] * state_mod
        base_score = base_metrics['score'] * difficulty_mod['score'] * state_mod
        base_response_time = base_metrics['response_time'] * difficulty_mod['response_time']
        
        # Add noise and constraints
        confidence = max(0.0, min(1.0, base_confidence + random.gauss(0, 0.12)))
        overall_score = max(0.0, min(1.0, base_score + random.gauss(0, 0.15)))
        response_time = max(50, base_response_time + random.gauss(0, 80))
        
        # Determine match type based on performance
        if confidence > 0.9:
            match_type = 'exact'
            exact_match = True
        elif confidence > 0.7:
            match_type = random.choice(['fuzzy', 'exact'])
            exact_match = match_type == 'exact'
        elif confidence > 0.4:
            match_type = random.choice(['fuzzy', 'keyword', 'partial'])
            exact_match = False
        else:
            match_type = random.choice(['partial', 'none'])
            exact_match = False
            if match_type == 'none':
                confidence = 0.0
                overall_score = 0.0
        
        # Generate component scores
        semantic_similarity = max(0.0, min(1.0, overall_score + random.gauss(0, 0.08)))
        category_accuracy = 1.0 if random.random() < (0.9 if confidence > 0.5 else 0.3) else 0.0
        state_relevance = 1.0 if random.random() < state_mod else 0.0
        
        # Generate realistic answers
        if match_type == 'none':
            retrieved_answer = ""
        else:
            retrieved_answer = f"For {category} in {state}: [Detailed requirements and procedures would be provided here]"
        
        expected_answer = f"Complete {category} requirements for {state} including specific steps, fees, and timelines"
        
        sample_data.append({
            'test_id': f'test_{i+1:04d}',
            'persona': persona,
            'category': category,
            'state': state,
            'difficulty': difficulty,
            'original_question': original_question,
            'query_variation': query_variation,
            'expected_answer': expected_answer,
            'retrieved_answer': retrieved_answer,
            'response_time_ms': response_time,
            'match_type': match_type,
            'confidence': confidence,
            'exact_match': exact_match,
            'category_match': category_accuracy == 1.0,
            'state_match': state_relevance == 1.0
        })
    
    return sample_data


class StandaloneAnalysisPipeline:
    """Standalone analysis pipeline that doesn't require database connectivity."""
    
    def __init__(self, output_dir: str = "tests/reports"):
        """Initialize the standalone pipeline."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results_files = {}
    
    async def analyze_responses_standalone(self, test_data: List[Dict[str, Any]]) -> str:
        """Analyze responses without database dependency."""
        from performance_analyzer import AnalyzedResponse, ScoringRubric
        
        analyzed_responses = []
        
        for test_item in test_data:
            # Create scoring rubric manually
            rubric = ScoringRubric()
            
            # Calculate scores based on test data
            rubric.exact_match = 1.0 if test_item.get('exact_match', False) else 0.0
            rubric.semantic_similarity = self._calculate_semantic_similarity(
                test_item.get('expected_answer', ''),
                test_item.get('retrieved_answer', '')
            )
            rubric.category_accuracy = 1.0 if test_item.get('category_match', False) else 0.0
            rubric.state_relevance = 1.0 if test_item.get('state_match', False) else 0.0
            
            # Quality scores
            rubric.completeness = self._calculate_completeness(
                test_item.get('expected_answer', ''),
                test_item.get('retrieved_answer', '')
            )
            rubric.relevance = max(rubric.semantic_similarity, rubric.exact_match)
            rubric.clarity = self._calculate_clarity(test_item.get('retrieved_answer', ''))
            rubric.authority = self._calculate_authority(
                test_item.get('retrieved_answer', ''),
                test_item.get('category', ''),
                test_item.get('state', '')
            )
            
            # Performance scores
            rubric.response_time_score = self._calculate_response_time_score(
                test_item.get('response_time_ms', 0)
            )
            rubric.confidence_score = test_item.get('confidence', 0.0)
            
            # Calculate overall score
            rubric.calculate_overall_score()
            
            # Create analyzed response
            analyzed_response = AnalyzedResponse(
                test_id=test_item['test_id'],
                timestamp=datetime.now(),
                persona=test_item.get('persona', ''),
                category=test_item.get('category', ''),
                state=test_item.get('state', ''),
                difficulty=test_item.get('difficulty', 'medium'),
                original_question=test_item.get('original_question', ''),
                query_variation=test_item.get('query_variation', ''),
                expected_answer=test_item.get('expected_answer', ''),
                retrieved_answer=test_item.get('retrieved_answer', ''),
                response_time_ms=test_item.get('response_time_ms', 0),
                match_type=test_item.get('match_type', 'none'),
                system_confidence=test_item.get('confidence', 0.0),
                scoring_rubric=rubric,
                failure_reasons=self._identify_failure_reasons(rubric, test_item),
                improvement_suggestions=self._generate_improvement_suggestions(rubric, test_item),
                performance_tier=self._classify_performance_tier(rubric.overall_score)
            )
            
            analyzed_responses.append(analyzed_response)
        
        # Save results
        results_data = {
            'metadata': {
                'analysis_timestamp': datetime.now().isoformat(),
                'total_responses': len(analyzed_responses),
                'analyzer_version': '1.0.0-standalone'
            },
            'analyzed_responses': [resp.to_dict() for resp in analyzed_responses]
        }
        
        analysis_file = self.output_dir / f"performance_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(analysis_file, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        return str(analysis_file)
    
    def _calculate_semantic_similarity(self, expected: str, retrieved: str) -> float:
        """Calculate semantic similarity score."""
        if not expected or not retrieved:
            return 0.0
        
        expected_words = set(expected.lower().split())
        retrieved_words = set(retrieved.lower().split())
        
        if not expected_words or not retrieved_words:
            return 0.0
        
        intersection = expected_words.intersection(retrieved_words)
        union = expected_words.union(retrieved_words)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_completeness(self, expected: str, retrieved: str) -> float:
        """Calculate completeness score."""
        if not expected or not retrieved:
            return 0.0
        
        # Simple completeness based on length ratio and key word presence
        length_ratio = min(1.0, len(retrieved) / len(expected)) if expected else 0.0
        
        # Check for key information markers
        key_markers = ['requirement', 'fee', 'hour', 'exam', 'renewal', 'license']
        expected_markers = sum(1 for marker in key_markers if marker in expected.lower())
        retrieved_markers = sum(1 for marker in key_markers if marker in retrieved.lower())
        
        marker_score = retrieved_markers / expected_markers if expected_markers > 0 else 0.5
        
        return (length_ratio * 0.6 + marker_score * 0.4)
    
    def _calculate_clarity(self, text: str) -> float:
        """Calculate clarity score."""
        if not text:
            return 0.0
        
        # Basic readability metrics
        sentences = len([s for s in text.split('.') if s.strip()])
        words = len(text.split())
        
        if sentences == 0 or words == 0:
            return 0.0
        
        # Average sentence length (optimal around 15-20 words)
        avg_sentence_length = words / sentences
        length_score = 1.0 - abs(avg_sentence_length - 17.5) / 17.5
        length_score = max(0.0, min(1.0, length_score))
        
        return length_score
    
    def _calculate_authority(self, text: str, category: str, state: str) -> float:
        """Calculate authority score."""
        if not text:
            return 0.0
        
        score = 0.5  # Base score
        text_lower = text.lower()
        
        # Authority markers
        authority_markers = ['official', 'regulation', 'statute', 'department', 'commission']
        marker_count = sum(1 for marker in authority_markers if marker in text_lower)
        score += min(0.3, marker_count * 0.1)
        
        # State and category relevance
        if state and state.lower() in text_lower:
            score += 0.1
        if category and category.lower() in text_lower:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_response_time_score(self, response_time_ms: float) -> float:
        """Calculate response time performance score."""
        if response_time_ms <= 100:
            return 1.0
        elif response_time_ms <= 300:
            return 0.8
        elif response_time_ms <= 1000:
            return 0.4
        else:
            return 0.1
    
    def _identify_failure_reasons(self, rubric, test_item: Dict[str, Any]) -> List[str]:
        """Identify failure reasons."""
        reasons = []
        
        if rubric.exact_match < 0.1:
            reasons.append("No exact match found")
        if rubric.semantic_similarity < 0.5:
            reasons.append("Low semantic similarity")
        if rubric.completeness < 0.5:
            reasons.append("Incomplete response")
        if rubric.response_time_score < 0.5:
            reasons.append("Poor response time")
        if not test_item.get('retrieved_answer'):
            reasons.append("No answer retrieved")
        
        return reasons
    
    def _generate_improvement_suggestions(self, rubric, test_item: Dict[str, Any]) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []
        
        if rubric.semantic_similarity < 0.7:
            suggestions.append("Improve semantic matching algorithms")
        if rubric.completeness < 0.7:
            suggestions.append("Expand answer completeness")
        if rubric.response_time_score < 0.6:
            suggestions.append("Optimize response time performance")
        if rubric.state_relevance < 0.6:
            suggestions.append(f"Add more {test_item.get('state', '')}-specific content")
        
        return suggestions
    
    def _classify_performance_tier(self, overall_score: float) -> str:
        """Classify performance tier."""
        if overall_score >= 0.85:
            return "excellent"
        elif overall_score >= 0.70:
            return "good"
        elif overall_score >= 0.50:
            return "needs_improvement"
        else:
            return "poor"
    
    async def run_full_analysis(self, test_size: int = 200) -> Dict[str, str]:
        """Run the complete standalone analysis."""
        
        logger.info("🚀 Starting FACT Standalone Performance Analysis")
        logger.info("=" * 60)
        
        # Generate test data
        logger.info(f"📝 Generating {test_size} test records...")
        test_data = generate_comprehensive_test_data(test_size)
        logger.info(f"✅ Test data generated: {len(test_data)} records")
        
        # Run performance analysis
        logger.info("🔍 Running performance analysis...")
        performance_file = await self.analyze_responses_standalone(test_data)
        self.results_files['performance_analysis'] = performance_file
        logger.info(f"✅ Performance analysis complete")
        
        # Run statistical analysis
        logger.info("📊 Running statistical analysis...")
        from statistical_reporter import StatisticalReporter
        
        statistical_reporter = StatisticalReporter()
        statistical_reporter.load_analyzed_data(performance_file)
        statistical_summary = statistical_reporter.generate_statistical_summary()
        
        stats_file = self.output_dir / f"statistical_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        statistical_reporter.save_statistical_report(statistical_summary, str(stats_file))
        self.results_files['statistical_analysis'] = str(stats_file)
        logger.info(f"✅ Statistical analysis complete")
        
        # Run weakness detection
        logger.info("🔍 Running weakness detection...")
        from weakness_detector import WeaknessDetector
        
        weakness_detector = WeaknessDetector()
        weakness_detector.load_analyzed_data(performance_file)
        weakness_report = weakness_detector.generate_weakness_report()
        
        weakness_file = self.output_dir / f"weakness_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        weakness_detector.save_weakness_report(weakness_report, str(weakness_file))
        self.results_files['weakness_analysis'] = str(weakness_file)
        logger.info(f"✅ Weakness analysis complete")
        
        # Generate comprehensive report
        logger.info("📝 Generating comprehensive report...")
        from report_generator import ReportGenerator
        
        report_generator = ReportGenerator()
        report_generator.load_analysis_data(
            performance_file=performance_file,
            statistical_file=str(stats_file),
            weakness_file=str(weakness_file)
        )
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.output_dir / f"comprehensive_fact_analysis_report_{timestamp}.md"
        dashboard_file = self.output_dir / f"dashboard_data_{timestamp}.json"
        
        comprehensive_report = report_generator.generate_comprehensive_report(str(report_file))
        dashboard_data = report_generator.generate_dashboard_data(str(dashboard_file))
        
        self.results_files['comprehensive_report'] = str(report_file)
        self.results_files['dashboard_data'] = str(dashboard_file)
        logger.info(f"✅ Comprehensive report generated")
        
        # Print summary
        self._print_summary(statistical_summary, weakness_report)
        
        return self.results_files
    
    def _print_summary(self, stats_data: Dict[str, Any], weakness_data: Dict[str, Any]):
        """Print analysis summary."""
        
        print("\n" + "=" * 80)
        print("FACT SYSTEM PERFORMANCE ANALYSIS - SUMMARY REPORT")
        print("=" * 80)
        
        # Overall performance
        overall = stats_data.get('overall_metrics', {})
        print(f"\n📊 OVERALL PERFORMANCE:")
        print(f"   Pass Rate: {overall.get('pass_rate', 0)*100:.1f}%")
        print(f"   Average Score: {overall.get('avg_score', 0):.3f}")
        print(f"   Total Responses: {stats_data.get('metadata', {}).get('total_responses', 'N/A')}")
        
        # Grade distribution
        if 'grade_distribution' in overall:
            print(f"\n📈 GRADE DISTRIBUTION:")
            for grade, count in overall['grade_distribution'].items():
                print(f"   {grade}: {count}")
        
        # Top categories
        category_analysis = stats_data.get('category_analysis', {})
        if category_analysis:
            print(f"\n🏆 TOP PERFORMING CATEGORIES:")
            sorted_cats = sorted(category_analysis.items(), key=lambda x: x[1]['avg_score'], reverse=True)
            for cat, stats in sorted_cats[:3]:
                print(f"   {cat}: {stats['avg_score']:.3f} ({stats['pass_rate']*100:.1f}% pass rate)")
        
        # Weakness summary
        exec_summary = weakness_data.get('executive_summary', {})
        print(f"\n🔍 WEAKNESS ANALYSIS:")
        print(f"   Critical Issues: {exec_summary.get('critical_issues', 0)}")
        print(f"   High Priority: {exec_summary.get('high_priority_issues', 0)}")
        print(f"   Knowledge Gaps: {exec_summary.get('total_knowledge_gaps', 0)}")
        print(f"   System Issues: {exec_summary.get('total_weakness_patterns', 0)}")
        
        print(f"\n📁 GENERATED FILES:")
        for file_type, file_path in self.results_files.items():
            print(f"   - {file_type}: {Path(file_path).name}")
        
        print("=" * 80)
        print("✅ Analysis complete! Check the comprehensive report for detailed insights.")


async def main():
    """Run standalone analysis demo."""
    
    # Configure logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    try:
        pipeline = StandaloneAnalysisPipeline("reports")
        results = await pipeline.run_full_analysis(test_size=150)
        
        print(f"\n🎉 Analysis pipeline completed successfully!")
        print(f"📂 Results saved to: tests/reports/")
        
        return results
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return {}


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
FACT System Statistical Analysis and Reporting Module

This module provides comprehensive statistical analysis of FACT performance data,
including persona comparisons, category analysis, state coverage, and trend identification.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from collections import defaultdict, Counter
import structlog
from dataclasses import dataclass, asdict
import scipy.stats as stats
from performance_analyzer import AnalyzedResponse, ScoringRubric

logger = structlog.get_logger(__name__)


@dataclass 
class CategoryStats:
    """Statistical metrics for a specific category."""
    category_name: str
    total_tests: int
    pass_rate: float
    avg_score: float
    median_score: float
    std_dev: float
    score_distribution: Dict[str, int]  # Grade distribution
    avg_response_time: float
    worst_performers: List[str]  # Question IDs
    improvement_potential: float


@dataclass
class PersonaStats:
    """Statistical metrics for a specific persona."""
    persona_name: str
    total_tests: int
    pass_rate: float
    avg_score: float
    strengths: List[str]  # Strong categories
    weaknesses: List[str]  # Weak categories
    category_performance: Dict[str, float]
    response_time_profile: Dict[str, float]
    confidence_levels: Dict[str, float]


@dataclass
class StateStats:
    """Statistical metrics for state coverage."""
    state_code: str
    total_tests: int
    coverage_percentage: float
    pass_rate: float
    avg_score: float
    missing_topics: List[str]
    strongest_categories: List[str]
    weakest_categories: List[str]


@dataclass
class PerformanceDistribution:
    """Statistical distribution of performance metrics."""
    metric_name: str
    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    percentile_25: float
    percentile_75: float
    percentile_95: float
    percentile_99: float
    skewness: float
    kurtosis: float


@dataclass
class ComparisonAnalysis:
    """Statistical comparison between different groups."""
    group_a: str
    group_b: str
    metric: str
    group_a_mean: float
    group_b_mean: float
    difference: float
    percentage_difference: float
    statistical_significance: float  # p-value
    effect_size: float  # Cohen's d
    significant: bool


class StatisticalReporter:
    """Comprehensive statistical analysis and reporting for FACT performance data."""
    
    def __init__(self):
        """Initialize the statistical reporter."""
        self.analyzed_responses: List[AnalyzedResponse] = []
        self.category_stats: Dict[str, CategoryStats] = {}
        self.persona_stats: Dict[str, PersonaStats] = {}
        self.state_stats: Dict[str, StateStats] = {}
        self.overall_distribution: Dict[str, PerformanceDistribution] = {}
        self.comparisons: List[ComparisonAnalysis] = []
        
    def load_analyzed_data(self, filepath: str):
        """Load analyzed response data from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Convert to AnalyzedResponse objects
        analyzed_responses = []
        for resp_data in data['analyzed_responses']:
            rubric_data = resp_data['scoring_rubric']
            rubric = ScoringRubric(**rubric_data)
            
            resp_data['scoring_rubric'] = rubric
            resp_data['timestamp'] = datetime.fromisoformat(resp_data['timestamp'])
            
            analyzed_response = AnalyzedResponse(**resp_data)
            analyzed_responses.append(analyzed_response)
        
        self.analyzed_responses = analyzed_responses
        logger.info(f"Loaded {len(analyzed_responses)} analyzed responses for statistical analysis")
    
    def convert_to_dataframe(self) -> pd.DataFrame:
        """Convert analyzed responses to pandas DataFrame for analysis."""
        records = []
        
        for resp in self.analyzed_responses:
            record = {
                'test_id': resp.test_id,
                'persona': resp.persona,
                'category': resp.category,
                'state': resp.state,
                'difficulty': resp.difficulty,
                'response_time_ms': resp.response_time_ms,
                'match_type': resp.match_type,
                'system_confidence': resp.system_confidence,
                'performance_tier': resp.performance_tier,
                
                # Scoring rubric metrics
                'exact_match': resp.scoring_rubric.exact_match,
                'semantic_similarity': resp.scoring_rubric.semantic_similarity,
                'category_accuracy': resp.scoring_rubric.category_accuracy,
                'state_relevance': resp.scoring_rubric.state_relevance,
                'completeness': resp.scoring_rubric.completeness,
                'relevance': resp.scoring_rubric.relevance,
                'clarity': resp.scoring_rubric.clarity,
                'authority': resp.scoring_rubric.authority,
                'response_time_score': resp.scoring_rubric.response_time_score,
                'confidence_score': resp.scoring_rubric.confidence_score,
                'overall_score': resp.scoring_rubric.overall_score,
                'grade_letter': resp.scoring_rubric.grade_letter,
                
                # Metadata
                'num_failure_reasons': len(resp.failure_reasons),
                'num_suggestions': len(resp.improvement_suggestions)
            }
            records.append(record)
        
        return pd.DataFrame(records)
    
    def analyze_category_performance(self, df: pd.DataFrame) -> Dict[str, CategoryStats]:
        """Analyze performance by category."""
        category_stats = {}
        
        for category in df['category'].unique():
            if not category:  # Skip empty categories
                continue
                
            cat_data = df[df['category'] == category]
            
            # Basic statistics
            total_tests = len(cat_data)
            pass_rate = len(cat_data[cat_data['overall_score'] >= 0.7]) / total_tests
            scores = cat_data['overall_score'].values
            
            # Score distribution by grade
            grade_dist = cat_data['grade_letter'].value_counts().to_dict()
            
            # Worst performers (lowest scoring questions)
            worst_performers = cat_data.nsmallest(5, 'overall_score')['test_id'].tolist()
            
            # Improvement potential (how much low performers could improve)
            low_performers = cat_data[cat_data['overall_score'] < 0.6]
            improvement_potential = (0.8 - low_performers['overall_score'].mean()) if len(low_performers) > 0 else 0.0
            
            category_stats[category] = CategoryStats(
                category_name=category,
                total_tests=total_tests,
                pass_rate=pass_rate,
                avg_score=float(np.mean(scores)),
                median_score=float(np.median(scores)),
                std_dev=float(np.std(scores)),
                score_distribution=grade_dist,
                avg_response_time=float(cat_data['response_time_ms'].mean()),
                worst_performers=worst_performers,
                improvement_potential=improvement_potential
            )
        
        self.category_stats = category_stats
        return category_stats
    
    def analyze_persona_performance(self, df: pd.DataFrame) -> Dict[str, PersonaStats]:
        """Analyze performance by persona."""
        persona_stats = {}
        
        for persona in df['persona'].unique():
            if not persona:
                continue
                
            persona_data = df[df['persona'] == persona]
            
            # Basic statistics
            total_tests = len(persona_data)
            pass_rate = len(persona_data[persona_data['overall_score'] >= 0.7]) / total_tests
            avg_score = float(persona_data['overall_score'].mean())
            
            # Category performance breakdown
            category_performance = {}
            for category in persona_data['category'].unique():
                if category:
                    cat_persona_data = persona_data[persona_data['category'] == category]
                    category_performance[category] = float(cat_persona_data['overall_score'].mean())
            
            # Identify strengths and weaknesses
            sorted_categories = sorted(category_performance.items(), key=lambda x: x[1], reverse=True)
            strengths = [cat for cat, score in sorted_categories[:3] if score >= 0.7]
            weaknesses = [cat for cat, score in sorted_categories[-3:] if score < 0.6]
            
            # Response time profile
            response_time_profile = {
                'avg_time': float(persona_data['response_time_ms'].mean()),
                'median_time': float(persona_data['response_time_ms'].median()),
                'p95_time': float(persona_data['response_time_ms'].quantile(0.95))
            }
            
            # Confidence levels
            confidence_levels = {
                'avg_system_confidence': float(persona_data['system_confidence'].mean()),
                'avg_confidence_score': float(persona_data['confidence_score'].mean())
            }
            
            persona_stats[persona] = PersonaStats(
                persona_name=persona,
                total_tests=total_tests,
                pass_rate=pass_rate,
                avg_score=avg_score,
                strengths=strengths,
                weaknesses=weaknesses,
                category_performance=category_performance,
                response_time_profile=response_time_profile,
                confidence_levels=confidence_levels
            )
        
        self.persona_stats = persona_stats
        return persona_stats
    
    def analyze_state_coverage(self, df: pd.DataFrame) -> Dict[str, StateStats]:
        """Analyze state-specific coverage and performance."""
        state_stats = {}
        total_possible_tests = len(df)
        
        # Get all unique states and analyze each
        states_in_data = df['state'].unique()
        
        for state in states_in_data:
            if not state:
                continue
                
            state_data = df[df['state'] == state]
            
            # Coverage metrics
            total_tests = len(state_data)
            coverage_percentage = (total_tests / total_possible_tests) * 100
            
            # Performance metrics  
            pass_rate = len(state_data[state_data['overall_score'] >= 0.7]) / total_tests if total_tests > 0 else 0
            avg_score = float(state_data['overall_score'].mean()) if total_tests > 0 else 0
            
            # Category analysis for this state
            category_scores = state_data.groupby('category')['overall_score'].mean().sort_values(ascending=False)
            strongest_categories = category_scores.head(3).index.tolist()
            weakest_categories = category_scores.tail(3).index.tolist()
            
            # Identify missing topics (categories with low representation)
            category_counts = state_data['category'].value_counts()
            all_categories = df['category'].unique()
            missing_topics = [cat for cat in all_categories if cat and (cat not in category_counts or category_counts[cat] < 2)]
            
            state_stats[state] = StateStats(
                state_code=state,
                total_tests=total_tests,
                coverage_percentage=coverage_percentage,
                pass_rate=pass_rate,
                avg_score=avg_score,
                missing_topics=missing_topics,
                strongest_categories=strongest_categories,
                weakest_categories=weakest_categories
            )
        
        self.state_stats = state_stats
        return state_stats
    
    def analyze_performance_distributions(self, df: pd.DataFrame) -> Dict[str, PerformanceDistribution]:
        """Analyze statistical distributions of key performance metrics."""
        distributions = {}
        
        metrics_to_analyze = [
            'overall_score', 'semantic_similarity', 'completeness', 'clarity',
            'response_time_ms', 'system_confidence', 'exact_match'
        ]
        
        for metric in metrics_to_analyze:
            data = df[metric].dropna()
            
            if len(data) == 0:
                continue
            
            distributions[metric] = PerformanceDistribution(
                metric_name=metric,
                mean=float(data.mean()),
                median=float(data.median()),
                std_dev=float(data.std()),
                min_value=float(data.min()),
                max_value=float(data.max()),
                percentile_25=float(data.quantile(0.25)),
                percentile_75=float(data.quantile(0.75)),
                percentile_95=float(data.quantile(0.95)),
                percentile_99=float(data.quantile(0.99)),
                skewness=float(stats.skew(data)),
                kurtosis=float(stats.kurtosis(data))
            )
        
        self.overall_distribution = distributions
        return distributions
    
    def perform_comparative_analysis(self, df: pd.DataFrame) -> List[ComparisonAnalysis]:
        """Perform statistical comparisons between different groups."""
        comparisons = []
        
        # Persona comparisons
        personas = [p for p in df['persona'].unique() if p]
        if len(personas) >= 2:
            for i, persona_a in enumerate(personas):
                for persona_b in personas[i+1:]:
                    comparison = self._compare_groups(
                        df, 'persona', persona_a, persona_b, 'overall_score'
                    )
                    if comparison:
                        comparisons.append(comparison)
        
        # Category comparisons (compare top 3 vs bottom 3)
        category_scores = df.groupby('category')['overall_score'].mean().sort_values(ascending=False)
        if len(category_scores) >= 6:
            top_categories = category_scores.head(3).index.tolist()
            bottom_categories = category_scores.tail(3).index.tolist()
            
            top_data = df[df['category'].isin(top_categories)]
            bottom_data = df[df['category'].isin(bottom_categories)]
            
            comparison = self._compare_datasets(
                top_data, bottom_data, 'overall_score', 
                'Top Categories', 'Bottom Categories'
            )
            if comparison:
                comparisons.append(comparison)
        
        # Difficulty level comparisons
        difficulties = [d for d in df['difficulty'].unique() if d]
        if 'easy' in difficulties and 'hard' in difficulties:
            comparison = self._compare_groups(
                df, 'difficulty', 'easy', 'hard', 'overall_score'
            )
            if comparison:
                comparisons.append(comparison)
        
        self.comparisons = comparisons
        return comparisons
    
    def _compare_groups(self, df: pd.DataFrame, group_col: str, 
                       group_a: str, group_b: str, metric: str) -> Optional[ComparisonAnalysis]:
        """Compare two groups statistically."""
        group_a_data = df[df[group_col] == group_a][metric].dropna()
        group_b_data = df[df[group_col] == group_b][metric].dropna()
        
        if len(group_a_data) < 5 or len(group_b_data) < 5:
            return None
        
        return self._compare_datasets(group_a_data, group_b_data, metric, group_a, group_b)
    
    def _compare_datasets(self, data_a, data_b, metric: str, label_a: str, label_b: str) -> Optional[ComparisonAnalysis]:
        """Compare two datasets statistically."""
        if hasattr(data_a, 'values'):
            values_a = data_a.values
        else:
            values_a = data_a
            
        if hasattr(data_b, 'values'):
            values_b = data_b.values
        else:
            values_b = data_b
        
        if len(values_a) < 5 or len(values_b) < 5:
            return None
        
        # Calculate statistics
        mean_a = float(np.mean(values_a))
        mean_b = float(np.mean(values_b))
        difference = mean_a - mean_b
        percentage_diff = (difference / mean_b) * 100 if mean_b != 0 else 0
        
        # Statistical significance test
        try:
            t_stat, p_value = stats.ttest_ind(values_a, values_b)
            
            # Effect size (Cohen's d)
            pooled_std = np.sqrt((np.var(values_a) + np.var(values_b)) / 2)
            cohens_d = difference / pooled_std if pooled_std > 0 else 0
            
        except Exception as e:
            logger.warning(f"Statistical test failed: {e}")
            p_value = 1.0
            cohens_d = 0.0
        
        return ComparisonAnalysis(
            group_a=label_a,
            group_b=label_b,
            metric=metric,
            group_a_mean=mean_a,
            group_b_mean=mean_b,
            difference=difference,
            percentage_difference=percentage_diff,
            statistical_significance=float(p_value),
            effect_size=float(cohens_d),
            significant=p_value < 0.05
        )
    
    def identify_success_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify patterns in high-performing responses."""
        high_performers = df[df['overall_score'] >= 0.85]
        low_performers = df[df['overall_score'] <= 0.5]
        
        if len(high_performers) == 0:
            return {"error": "No high-performing responses to analyze"}
        
        patterns = {
            "high_performer_characteristics": {
                "total_count": len(high_performers),
                "avg_response_time": float(high_performers['response_time_ms'].mean()),
                "common_match_types": high_performers['match_type'].value_counts().head(3).to_dict(),
                "avg_confidence": float(high_performers['system_confidence'].mean()),
                "dominant_personas": high_performers['persona'].value_counts().head(3).to_dict(),
                "dominant_categories": high_performers['category'].value_counts().head(3).to_dict()
            },
            "low_performer_characteristics": {
                "total_count": len(low_performers),
                "avg_response_time": float(low_performers['response_time_ms'].mean()) if len(low_performers) > 0 else 0,
                "common_match_types": low_performers['match_type'].value_counts().head(3).to_dict() if len(low_performers) > 0 else {},
                "avg_confidence": float(low_performers['system_confidence'].mean()) if len(low_performers) > 0 else 0
            }
        }
        
        return patterns
    
    def generate_statistical_summary(self) -> Dict[str, Any]:
        """Generate comprehensive statistical summary."""
        df = self.convert_to_dataframe()
        
        # Run all analyses
        self.analyze_category_performance(df)
        self.analyze_persona_performance(df) 
        self.analyze_state_coverage(df)
        self.analyze_performance_distributions(df)
        self.perform_comparative_analysis(df)
        success_patterns = self.identify_success_patterns(df)
        
        summary = {
            "metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "total_responses": len(df),
                "unique_personas": len(df['persona'].unique()),
                "unique_categories": len(df['category'].unique()),
                "unique_states": len(df['state'].unique())
            },
            "overall_metrics": {
                "avg_score": float(df['overall_score'].mean()),
                "median_score": float(df['overall_score'].median()),
                "pass_rate": len(df[df['overall_score'] >= 0.7]) / len(df),
                "grade_distribution": df['grade_letter'].value_counts().to_dict()
            },
            "category_analysis": {cat: asdict(stats) for cat, stats in self.category_stats.items()},
            "persona_analysis": {persona: asdict(stats) for persona, stats in self.persona_stats.items()},
            "state_analysis": {state: asdict(stats) for state, stats in self.state_stats.items()},
            "performance_distributions": {metric: asdict(dist) for metric, dist in self.overall_distribution.items()},
            "comparative_analysis": [asdict(comp) for comp in self.comparisons],
            "success_patterns": success_patterns
        }
        
        return summary
    
    def save_statistical_report(self, summary: Dict[str, Any], filepath: str):
        """Save statistical analysis to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Statistical analysis saved to {filepath}")


async def main():
    """Test the statistical reporter."""
    # This would normally load real analyzed data
    print("Statistical Reporter - Demo Mode")
    print("In production, this would load analyzed response data and generate comprehensive statistics")
    
    reporter = StatisticalReporter()
    
    # Create sample data for demonstration
    sample_data = {
        'analyzed_responses': [
            {
                'test_id': 'test_001',
                'timestamp': datetime.now().isoformat(),
                'persona': 'insurance_agent',
                'category': 'licensing',
                'state': 'CA',
                'difficulty': 'medium',
                'original_question': 'Sample question',
                'query_variation': 'Sample variation',
                'expected_answer': 'Sample expected',
                'retrieved_answer': 'Sample retrieved',
                'response_time_ms': 150.0,
                'match_type': 'fuzzy',
                'system_confidence': 0.85,
                'scoring_rubric': {
                    'exact_match': 0.0,
                    'semantic_similarity': 0.8,
                    'category_accuracy': 1.0,
                    'state_relevance': 0.9,
                    'completeness': 0.7,
                    'relevance': 0.8,
                    'clarity': 0.75,
                    'authority': 0.8,
                    'response_time_score': 0.9,
                    'confidence_score': 0.85,
                    'overall_score': 0.82,
                    'grade_letter': 'B+'
                },
                'failure_reasons': [],
                'improvement_suggestions': ['Improve exact matching'],
                'performance_tier': 'good'
            }
        ]
    }
    
    # Save sample data and load it
    with open('tests/sample_analyzed_data.json', 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    # Load and analyze
    reporter.load_analyzed_data('tests/sample_analyzed_data.json')
    summary = reporter.generate_statistical_summary()
    
    print(f"✅ Generated statistical summary with {summary['metadata']['total_responses']} responses")
    print(f"📊 Overall pass rate: {summary['overall_metrics']['pass_rate']*100:.1f}%")
    
    # Save report
    reporter.save_statistical_report(summary, 'tests/statistical_analysis_report.json')
    print("📝 Statistical analysis saved to tests/statistical_analysis_report.json")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
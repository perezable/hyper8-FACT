"""
Quality Metrics Calculator for FACT System Response Evaluation
Comprehensive metrics and analytics for response quality assessment.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

from ..core.response_evaluator import EvaluationResult
from ..config.scoring_rubric import ScoreDimension, PersonaType

@dataclass
class QualityMetrics:
    """Comprehensive quality metrics for response evaluation."""
    
    # Overall metrics
    total_responses: int
    average_score: float
    median_score: float
    score_std_dev: float
    confidence_average: float
    
    # Score distribution
    score_distribution: Dict[str, int]  # excellent, good, adequate, poor, failed
    
    # Dimension metrics
    dimension_averages: Dict[str, float]
    dimension_correlations: Dict[str, float]
    
    # Persona-specific metrics
    persona_performance: Dict[str, Dict[str, float]]
    
    # Quality indicators
    high_confidence_percentage: float
    consistency_score: float
    improvement_trend: Optional[float]
    
    # Detailed analytics
    top_performing_areas: List[str]
    areas_for_improvement: List[str]
    quality_insights: List[str]

@dataclass
class TrendAnalysis:
    """Trend analysis for response quality over time."""
    time_period: str
    trend_direction: str  # improving, declining, stable
    trend_strength: float  # 0-1
    change_rate: float
    significant_changes: List[Dict[str, Any]]

class QualityMetricsCalculator:
    """Calculator for comprehensive quality metrics and analytics."""
    
    def __init__(self):
        self.score_thresholds = {
            "excellent": (90, 100),
            "good": (70, 89),
            "adequate": (50, 69),
            "poor": (30, 49),
            "failed": (0, 29)
        }
    
    def calculate_metrics(
        self,
        evaluation_results: List[EvaluationResult],
        include_trends: bool = True,
        time_window_days: int = 30
    ) -> QualityMetrics:
        """
        Calculate comprehensive quality metrics from evaluation results.
        
        Args:
            evaluation_results: List of evaluation results
            include_trends: Whether to include trend analysis
            time_window_days: Time window for trend analysis
            
        Returns:
            QualityMetrics with comprehensive analytics
        """
        if not evaluation_results:
            return self._empty_metrics()
        
        # Convert to DataFrame for easier analysis
        df = self._results_to_dataframe(evaluation_results)
        
        # Calculate basic metrics
        basic_metrics = self._calculate_basic_metrics(df)
        
        # Calculate dimension metrics
        dimension_metrics = self._calculate_dimension_metrics(df)
        
        # Calculate persona metrics
        persona_metrics = self._calculate_persona_metrics(df)
        
        # Calculate quality indicators
        quality_indicators = self._calculate_quality_indicators(df)
        
        # Generate insights
        insights = self._generate_quality_insights(df, basic_metrics, dimension_metrics)
        
        # Calculate trend if requested
        improvement_trend = None
        if include_trends and len(evaluation_results) > 10:
            improvement_trend = self._calculate_improvement_trend(df, time_window_days)
        
        return QualityMetrics(
            **basic_metrics,
            **dimension_metrics,
            **persona_metrics,
            **quality_indicators,
            improvement_trend=improvement_trend,
            quality_insights=insights
        )
    
    def _results_to_dataframe(self, results: List[EvaluationResult]) -> pd.DataFrame:
        """Convert evaluation results to pandas DataFrame."""
        data = []
        for result in results:
            row = {
                'response_id': result.response_id,
                'weighted_score': result.weighted_score,
                'confidence_score': result.confidence_score,
                'persona': result.persona.value,
                'timestamp': result.timestamp,
                'score_category': result.score_category
            }
            
            # Add dimension scores
            for dim, score in result.dimension_scores.items():
                row[f'dim_{dim}'] = score
            
            data.append(row)
        
        return pd.DataFrame(data)
    
    def _calculate_basic_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic quality metrics."""
        scores = df['weighted_score']
        
        # Score distribution
        score_distribution = {}
        for category, (min_score, max_score) in self.score_thresholds.items():
            count = len(df[(df['weighted_score'] >= min_score) & 
                          (df['weighted_score'] <= max_score)])
            score_distribution[category] = count
        
        return {
            'total_responses': len(df),
            'average_score': float(scores.mean()),
            'median_score': float(scores.median()),
            'score_std_dev': float(scores.std()),
            'confidence_average': float(df['confidence_score'].mean()),
            'score_distribution': score_distribution
        }
    
    def _calculate_dimension_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate dimension-specific metrics."""
        dimension_columns = [col for col in df.columns if col.startswith('dim_')]
        
        # Calculate averages
        dimension_averages = {}
        for col in dimension_columns:
            dim_name = col.replace('dim_', '')
            dimension_averages[dim_name] = float(df[col].mean())
        
        # Calculate correlations with overall score
        dimension_correlations = {}
        for col in dimension_columns:
            dim_name = col.replace('dim_', '')
            correlation = df[col].corr(df['weighted_score'])
            dimension_correlations[dim_name] = float(correlation) if not pd.isna(correlation) else 0.0
        
        return {
            'dimension_averages': dimension_averages,
            'dimension_correlations': dimension_correlations
        }
    
    def _calculate_persona_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate persona-specific performance metrics."""
        persona_performance = {}
        
        for persona in df['persona'].unique():
            persona_df = df[df['persona'] == persona]
            
            persona_performance[persona] = {
                'count': len(persona_df),
                'average_score': float(persona_df['weighted_score'].mean()),
                'median_score': float(persona_df['weighted_score'].median()),
                'std_dev': float(persona_df['weighted_score'].std()),
                'confidence_avg': float(persona_df['confidence_score'].mean())
            }
        
        return {'persona_performance': persona_performance}
    
    def _calculate_quality_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate quality indicator metrics."""
        
        # High confidence percentage (confidence > 0.8)
        high_confidence_count = len(df[df['confidence_score'] > 0.8])
        high_confidence_percentage = (high_confidence_count / len(df)) * 100
        
        # Consistency score (based on score standard deviation)
        # Lower std dev = higher consistency
        max_std_dev = 30.0  # Reasonable maximum
        consistency_score = max(0, 100 - (df['weighted_score'].std() / max_std_dev) * 100)
        
        return {
            'high_confidence_percentage': float(high_confidence_percentage),
            'consistency_score': float(consistency_score)
        }
    
    def _calculate_improvement_trend(self, df: pd.DataFrame, time_window_days: int) -> float:
        """Calculate improvement trend over time."""
        if 'timestamp' not in df.columns:
            return 0.0
        
        # Sort by timestamp
        df_sorted = df.sort_values('timestamp')
        
        # Split into time periods
        cutoff_date = datetime.now() - timedelta(days=time_window_days // 2)
        early_period = df_sorted[df_sorted['timestamp'] < cutoff_date]
        recent_period = df_sorted[df_sorted['timestamp'] >= cutoff_date]
        
        if len(early_period) == 0 or len(recent_period) == 0:
            return 0.0
        
        early_avg = early_period['weighted_score'].mean()
        recent_avg = recent_period['weighted_score'].mean()
        
        # Calculate percentage change
        if early_avg > 0:
            improvement_trend = ((recent_avg - early_avg) / early_avg) * 100
            return float(improvement_trend)
        
        return 0.0
    
    def _generate_quality_insights(
        self, 
        df: pd.DataFrame,
        basic_metrics: Dict[str, Any],
        dimension_metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable quality insights."""
        insights = []
        
        # Overall performance insights
        avg_score = basic_metrics['average_score']
        if avg_score >= 85:
            insights.append("Overall response quality is excellent - maintain current standards")
        elif avg_score >= 70:
            insights.append("Good response quality with room for improvement")
        elif avg_score >= 50:
            insights.append("Adequate response quality - focus on key improvement areas")
        else:
            insights.append("Response quality needs significant improvement")
        
        # Dimension-specific insights
        dim_averages = dimension_metrics['dimension_averages']
        lowest_dim = min(dim_averages.items(), key=lambda x: x[1])
        highest_dim = max(dim_averages.items(), key=lambda x: x[1])
        
        insights.append(f"Strongest dimension: {highest_dim[0]} ({highest_dim[1]:.1f}/100)")
        insights.append(f"Weakest dimension: {lowest_dim[0]} ({lowest_dim[1]:.1f}/100)")
        
        if lowest_dim[1] < 60:
            insights.append(f"Priority improvement area: {lowest_dim[0]} - consider targeted training")
        
        # Consistency insights
        std_dev = basic_metrics['score_std_dev']
        if std_dev > 20:
            insights.append("High score variability detected - review evaluation consistency")
        elif std_dev < 10:
            insights.append("Good response consistency across evaluations")
        
        # Confidence insights
        conf_avg = basic_metrics['confidence_average']
        if conf_avg < 0.7:
            insights.append("Low evaluation confidence - consider additional training data")
        elif conf_avg > 0.9:
            insights.append("High evaluation confidence - metrics are reliable")
        
        return insights
    
    def _empty_metrics(self) -> QualityMetrics:
        """Return empty metrics when no data is available."""
        return QualityMetrics(
            total_responses=0,
            average_score=0.0,
            median_score=0.0,
            score_std_dev=0.0,
            confidence_average=0.0,
            score_distribution={},
            dimension_averages={},
            dimension_correlations={},
            persona_performance={},
            high_confidence_percentage=0.0,
            consistency_score=0.0,
            improvement_trend=None,
            top_performing_areas=[],
            areas_for_improvement=[],
            quality_insights=["No evaluation data available"]
        )
    
    def calculate_trend_analysis(
        self,
        evaluation_results: List[EvaluationResult],
        time_periods: List[str] = ["7d", "30d", "90d"]
    ) -> Dict[str, TrendAnalysis]:
        """Calculate detailed trend analysis for different time periods."""
        if not evaluation_results:
            return {}
        
        df = self._results_to_dataframe(evaluation_results)
        trends = {}
        
        for period in time_periods:
            days = int(period.replace('d', ''))
            cutoff_date = datetime.now() - timedelta(days=days)
            
            recent_data = df[df['timestamp'] >= cutoff_date]
            if len(recent_data) < 5:  # Need minimum data points
                continue
            
            # Calculate trend
            recent_data = recent_data.sort_values('timestamp')
            scores = recent_data['weighted_score'].values
            
            # Simple linear regression for trend
            if len(scores) > 1:
                x = np.arange(len(scores))
                slope, intercept = np.polyfit(x, scores, 1)
                
                # Determine trend direction
                if slope > 0.5:
                    direction = "improving"
                elif slope < -0.5:
                    direction = "declining"
                else:
                    direction = "stable"
                
                # Calculate trend strength
                correlation = np.corrcoef(x, scores)[0, 1]
                trend_strength = abs(correlation) if not np.isnan(correlation) else 0.0
                
                # Calculate change rate (points per day)
                change_rate = slope
                
                trends[period] = TrendAnalysis(
                    time_period=period,
                    trend_direction=direction,
                    trend_strength=trend_strength,
                    change_rate=change_rate,
                    significant_changes=self._identify_significant_changes(recent_data)
                )
        
        return trends
    
    def _identify_significant_changes(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify significant changes in the data."""
        changes = []
        
        if len(df) < 10:
            return changes
        
        # Look for significant score jumps
        scores = df['weighted_score'].values
        for i in range(1, len(scores)):
            change = abs(scores[i] - scores[i-1])
            if change > 20:  # Significant change threshold
                changes.append({
                    'type': 'score_jump',
                    'magnitude': change,
                    'direction': 'increase' if scores[i] > scores[i-1] else 'decrease',
                    'timestamp': df.iloc[i]['timestamp'].isoformat()
                })
        
        return changes
    
    def generate_quality_report(
        self,
        evaluation_results: List[EvaluationResult],
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """Generate a comprehensive quality report."""
        
        metrics = self.calculate_metrics(evaluation_results)
        trends = self.calculate_trend_analysis(evaluation_results)
        
        report = {
            'report_generated': datetime.now().isoformat(),
            'summary': {
                'total_evaluations': metrics.total_responses,
                'overall_quality': self._get_quality_rating(metrics.average_score),
                'average_score': metrics.average_score,
                'confidence_level': metrics.confidence_average
            },
            'metrics': asdict(metrics),
            'trends': {k: asdict(v) for k, v in trends.items()},
            'insights': metrics.quality_insights
        }
        
        if include_recommendations:
            report['recommendations'] = self._generate_recommendations(metrics, trends)
        
        return report
    
    def _get_quality_rating(self, score: float) -> str:
        """Convert numeric score to quality rating."""
        if score >= 90:
            return "Excellent"
        elif score >= 70:
            return "Good"
        elif score >= 50:
            return "Adequate"
        elif score >= 30:
            return "Poor"
        else:
            return "Needs Improvement"
    
    def _generate_recommendations(
        self,
        metrics: QualityMetrics,
        trends: Dict[str, TrendAnalysis]
    ) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on metrics and trends."""
        recommendations = []
        
        # Score-based recommendations
        if metrics.average_score < 70:
            recommendations.append({
                'category': 'Overall Quality',
                'priority': 'High',
                'recommendation': 'Implement comprehensive response quality training program',
                'expected_impact': 'Increase overall scores by 15-20 points'
            })
        
        # Dimension-specific recommendations
        for dim, score in metrics.dimension_averages.items():
            if score < 60:
                recommendations.append({
                    'category': f'{dim.replace("_", " ").title()} Improvement',
                    'priority': 'High' if score < 50 else 'Medium',
                    'recommendation': f'Focus training on {dim} - create specific guidelines and examples',
                    'expected_impact': f'Improve {dim} scores to 70+ range'
                })
        
        # Consistency recommendations
        if metrics.consistency_score < 70:
            recommendations.append({
                'category': 'Consistency',
                'priority': 'Medium',
                'recommendation': 'Standardize response templates and evaluation criteria',
                'expected_impact': 'Reduce score variability by 20-30%'
            })
        
        # Confidence recommendations
        if metrics.confidence_average < 0.7:
            recommendations.append({
                'category': 'Evaluation Confidence',
                'priority': 'Medium',
                'recommendation': 'Enhance AI training with more diverse examples',
                'expected_impact': 'Increase evaluation confidence to 80%+'
            })
        
        return recommendations

# Global metrics calculator instance
QUALITY_METRICS_CALCULATOR = QualityMetricsCalculator()
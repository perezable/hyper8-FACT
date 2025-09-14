"""
Evaluation Reporter for FACT System Response Evaluation
Generate comprehensive reports and visualizations for response quality assessment.
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from ..core.response_evaluator import EvaluationResult
from ..metrics.quality_metrics import QualityMetrics, TrendAnalysis, QUALITY_METRICS_CALCULATOR
from ..config.scoring_rubric import SCORING_RUBRIC, PersonaType, ScoreDimension

class EvaluationReporter:
    """Generate detailed reports and exports for evaluation results."""
    
    def __init__(self, output_dir: str = "evaluation_reports"):
        """
        Initialize the evaluation reporter.
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def generate_comprehensive_report(
        self,
        evaluation_results: List[EvaluationResult],
        report_name: str = None,
        include_raw_data: bool = True,
        include_visualizations: bool = True
    ) -> str:
        """
        Generate a comprehensive evaluation report.
        
        Args:
            evaluation_results: List of evaluation results
            report_name: Name for the report file
            include_raw_data: Include raw evaluation data
            include_visualizations: Include charts and graphs
            
        Returns:
            Path to the generated report file
        """
        if not report_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_name = f"evaluation_report_{timestamp}"
        
        # Calculate metrics
        metrics = QUALITY_METRICS_CALCULATOR.calculate_metrics(evaluation_results)
        trends = QUALITY_METRICS_CALCULATOR.calculate_trend_analysis(evaluation_results)
        
        # Generate report data
        report_data = {
            "metadata": {
                "report_name": report_name,
                "generated_at": datetime.now().isoformat(),
                "total_evaluations": len(evaluation_results),
                "evaluation_period": self._get_evaluation_period(evaluation_results),
                "report_version": "1.0.0"
            },
            "executive_summary": self._generate_executive_summary(metrics, trends),
            "quality_metrics": self._format_metrics_for_report(metrics),
            "trend_analysis": self._format_trends_for_report(trends),
            "dimension_analysis": self._generate_dimension_analysis(evaluation_results),
            "persona_analysis": self._generate_persona_analysis(evaluation_results),
            "recommendations": self._generate_detailed_recommendations(metrics, trends),
            "quality_insights": metrics.quality_insights
        }
        
        if include_raw_data:
            report_data["raw_evaluations"] = [
                self._format_evaluation_for_export(result) 
                for result in evaluation_results
            ]
        
        # Save report
        report_file = self.output_dir / f"{report_name}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        # Generate additional formats
        self._generate_html_report(report_data, report_name)
        self._generate_csv_export(evaluation_results, report_name)
        
        self.logger.info(f"Generated comprehensive report: {report_file}")
        return str(report_file)
    
    def generate_summary_dashboard(
        self,
        evaluation_results: List[EvaluationResult],
        dashboard_name: str = None
    ) -> str:
        """Generate a summary dashboard with key metrics."""
        
        if not dashboard_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dashboard_name = f"dashboard_{timestamp}"
        
        metrics = QUALITY_METRICS_CALCULATOR.calculate_metrics(evaluation_results)
        
        dashboard_data = {
            "title": "FACT System Quality Dashboard",
            "generated_at": datetime.now().isoformat(),
            "key_metrics": {
                "overall_score": {
                    "value": metrics.average_score,
                    "category": self._get_score_category(metrics.average_score),
                    "change": metrics.improvement_trend
                },
                "total_evaluations": metrics.total_responses,
                "confidence_level": metrics.confidence_average,
                "consistency_score": metrics.consistency_score
            },
            "score_breakdown": metrics.score_distribution,
            "dimension_performance": metrics.dimension_averages,
            "persona_performance": {
                persona: data["average_score"]
                for persona, data in metrics.persona_performance.items()
            },
            "top_insights": metrics.quality_insights[:5],
            "alerts": self._generate_quality_alerts(metrics)
        }
        
        dashboard_file = self.output_dir / f"{dashboard_name}_dashboard.json"
        with open(dashboard_file, 'w') as f:
            json.dump(dashboard_data, f, indent=2, default=str)
        
        return str(dashboard_file)
    
    def export_evaluation_data(
        self,
        evaluation_results: List[EvaluationResult],
        format: str = "csv",
        filename: str = None
    ) -> str:
        """
        Export evaluation data in various formats.
        
        Args:
            evaluation_results: List of evaluation results
            format: Export format (csv, json, xlsx)
            filename: Output filename
            
        Returns:
            Path to the exported file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"evaluation_data_{timestamp}"
        
        if format.lower() == "csv":
            return self._export_to_csv(evaluation_results, filename)
        elif format.lower() == "json":
            return self._export_to_json(evaluation_results, filename)
        elif format.lower() == "xlsx":
            return self._export_to_excel(evaluation_results, filename)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _generate_executive_summary(
        self,
        metrics: QualityMetrics,
        trends: Dict[str, TrendAnalysis]
    ) -> Dict[str, Any]:
        """Generate executive summary section."""
        
        # Determine overall status
        overall_status = "excellent" if metrics.average_score >= 85 else \
                        "good" if metrics.average_score >= 70 else \
                        "needs_improvement"
        
        # Find key trends
        key_trend = None
        if "30d" in trends:
            trend_30d = trends["30d"]
            key_trend = {
                "direction": trend_30d.trend_direction,
                "strength": trend_30d.trend_strength,
                "change_rate": trend_30d.change_rate
            }
        
        # Identify top priority
        weakest_dimension = min(metrics.dimension_averages.items(), key=lambda x: x[1])
        
        return {
            "overall_status": overall_status,
            "average_score": metrics.average_score,
            "total_responses_evaluated": metrics.total_responses,
            "key_trend": key_trend,
            "top_priority": {
                "area": weakest_dimension[0],
                "current_score": weakest_dimension[1],
                "improvement_needed": max(0, 70 - weakest_dimension[1])
            },
            "confidence_level": metrics.confidence_average,
            "consistency_rating": "high" if metrics.consistency_score > 80 else "medium" if metrics.consistency_score > 60 else "low"
        }
    
    def _format_metrics_for_report(self, metrics: QualityMetrics) -> Dict[str, Any]:
        """Format metrics for report display."""
        return {
            "overall_performance": {
                "average_score": metrics.average_score,
                "median_score": metrics.median_score,
                "standard_deviation": metrics.score_std_dev,
                "score_distribution": metrics.score_distribution
            },
            "dimension_performance": {
                "averages": metrics.dimension_averages,
                "correlations": metrics.dimension_correlations
            },
            "quality_indicators": {
                "high_confidence_percentage": metrics.high_confidence_percentage,
                "consistency_score": metrics.consistency_score,
                "improvement_trend": metrics.improvement_trend
            }
        }
    
    def _format_trends_for_report(self, trends: Dict[str, TrendAnalysis]) -> Dict[str, Any]:
        """Format trend analysis for report display."""
        formatted_trends = {}
        for period, trend in trends.items():
            formatted_trends[period] = {
                "direction": trend.trend_direction,
                "strength": trend.trend_strength,
                "change_rate": trend.change_rate,
                "significant_changes": len(trend.significant_changes)
            }
        return formatted_trends
    
    def _generate_dimension_analysis(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """Generate detailed dimension analysis."""
        dimension_analysis = {}
        
        for dimension in ScoreDimension:
            scores = []
            for result in results:
                if dimension.value in result.dimension_scores:
                    scores.append(result.dimension_scores[dimension.value])
            
            if scores:
                dimension_analysis[dimension.value] = {
                    "average": sum(scores) / len(scores),
                    "min": min(scores),
                    "max": max(scores),
                    "count": len(scores),
                    "weight": SCORING_RUBRIC.get_dimension_weight(dimension),
                    "description": SCORING_RUBRIC.dimensions[dimension].description
                }
        
        return dimension_analysis
    
    def _generate_persona_analysis(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """Generate detailed persona analysis."""
        persona_analysis = {}
        
        for persona in PersonaType:
            persona_results = [r for r in results if r.persona == persona]
            
            if persona_results:
                scores = [r.weighted_score for r in persona_results]
                persona_analysis[persona.value] = {
                    "count": len(persona_results),
                    "average_score": sum(scores) / len(scores),
                    "score_range": (min(scores), max(scores)),
                    "top_score": max(scores),
                    "improvement_areas": self._identify_persona_improvement_areas(persona_results)
                }
        
        return persona_analysis
    
    def _identify_persona_improvement_areas(self, results: List[EvaluationResult]) -> List[str]:
        """Identify improvement areas for a specific persona."""
        dimension_scores = {}
        
        for result in results:
            for dim, score in result.dimension_scores.items():
                if dim not in dimension_scores:
                    dimension_scores[dim] = []
                dimension_scores[dim].append(score)
        
        # Find dimensions with lowest average scores
        avg_scores = {dim: sum(scores)/len(scores) for dim, scores in dimension_scores.items()}
        sorted_dimensions = sorted(avg_scores.items(), key=lambda x: x[1])
        
        improvement_areas = []
        for dim, score in sorted_dimensions[:2]:  # Top 2 improvement areas
            if score < 70:
                improvement_areas.append(f"{dim.replace('_', ' ').title()}: {score:.1f}/100")
        
        return improvement_areas
    
    def _generate_detailed_recommendations(
        self,
        metrics: QualityMetrics,
        trends: Dict[str, TrendAnalysis]
    ) -> List[Dict[str, Any]]:
        """Generate detailed actionable recommendations."""
        recommendations = []
        
        # Overall score recommendations
        if metrics.average_score < 75:
            recommendations.append({
                "category": "Overall Quality",
                "priority": "High",
                "issue": f"Average score of {metrics.average_score:.1f} is below target of 75",
                "recommendation": "Implement comprehensive quality improvement program",
                "specific_actions": [
                    "Review and update response templates",
                    "Provide targeted training for low-scoring areas",
                    "Implement quality assurance processes"
                ],
                "expected_timeline": "4-6 weeks",
                "success_metrics": ["Increase average score to 75+", "Reduce score variability"]
            })
        
        # Dimension-specific recommendations
        for dim, score in metrics.dimension_averages.items():
            if score < 65:
                recommendations.append({
                    "category": f"{dim.replace('_', ' ').title()} Improvement",
                    "priority": "High" if score < 50 else "Medium",
                    "issue": f"Low {dim} score of {score:.1f}/100",
                    "recommendation": f"Focus improvement efforts on {dim}",
                    "specific_actions": self._get_dimension_specific_actions(dim),
                    "expected_timeline": "2-4 weeks",
                    "success_metrics": [f"Increase {dim} score to 70+"]
                })
        
        # Trend-based recommendations
        if "30d" in trends and trends["30d"].trend_direction == "declining":
            recommendations.append({
                "category": "Quality Trend",
                "priority": "High",
                "issue": "Quality scores showing declining trend",
                "recommendation": "Investigate and address quality degradation",
                "specific_actions": [
                    "Analyze recent changes in processes or staff",
                    "Implement immediate quality monitoring",
                    "Provide refresher training"
                ],
                "expected_timeline": "1-2 weeks",
                "success_metrics": ["Stabilize quality scores", "Reverse declining trend"]
            })
        
        return recommendations
    
    def _get_dimension_specific_actions(self, dimension: str) -> List[str]:
        """Get specific improvement actions for a dimension."""
        action_map = {
            "accuracy": [
                "Implement fact-checking processes",
                "Provide access to updated knowledge base",
                "Train on common accuracy pitfalls"
            ],
            "completeness": [
                "Create comprehensive response checklists",
                "Train on identifying all question components",
                "Implement review process for completeness"
            ],
            "relevance": [
                "Improve question understanding training",
                "Create relevance scoring guidelines",
                "Practice focused response techniques"
            ],
            "clarity": [
                "Provide writing and communication training",
                "Create clear response templates",
                "Implement readability standards"
            ],
            "persona_fit": [
                "Enhance persona understanding training",
                "Create persona-specific response guides",
                "Practice persona adaptation techniques"
            ]
        }
        return action_map.get(dimension, ["Review and improve response quality"])
    
    def _generate_quality_alerts(self, metrics: QualityMetrics) -> List[Dict[str, str]]:
        """Generate quality alerts for dashboard."""
        alerts = []
        
        # Score alerts
        if metrics.average_score < 60:
            alerts.append({
                "level": "critical",
                "message": f"Overall quality score critically low: {metrics.average_score:.1f}/100",
                "action": "Immediate intervention required"
            })
        elif metrics.average_score < 70:
            alerts.append({
                "level": "warning", 
                "message": f"Overall quality score below target: {metrics.average_score:.1f}/100",
                "action": "Quality improvement needed"
            })
        
        # Consistency alerts
        if metrics.consistency_score < 60:
            alerts.append({
                "level": "warning",
                "message": f"Low consistency score: {metrics.consistency_score:.1f}/100",
                "action": "Review evaluation standards"
            })
        
        # Confidence alerts
        if metrics.confidence_average < 0.6:
            alerts.append({
                "level": "warning",
                "message": f"Low evaluation confidence: {metrics.confidence_average:.1f}",
                "action": "Review AI training data"
            })
        
        return alerts
    
    def _get_evaluation_period(self, results: List[EvaluationResult]) -> Dict[str, str]:
        """Get the evaluation period from results."""
        if not results:
            return {}
        
        timestamps = [r.timestamp for r in results if r.timestamp]
        if not timestamps:
            return {}
        
        return {
            "start": min(timestamps).isoformat(),
            "end": max(timestamps).isoformat(),
            "duration_days": (max(timestamps) - min(timestamps)).days
        }
    
    def _get_score_category(self, score: float) -> str:
        """Get score category from numeric score."""
        if score >= 90:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 50:
            return "adequate"
        elif score >= 30:
            return "poor"
        else:
            return "failed"
    
    def _format_evaluation_for_export(self, result: EvaluationResult) -> Dict[str, Any]:
        """Format evaluation result for export."""
        return {
            "response_id": result.response_id,
            "question": result.question,
            "response": result.response,
            "persona": result.persona.value,
            "weighted_score": result.weighted_score,
            "score_category": result.score_category,
            "confidence_score": result.confidence_score,
            "timestamp": result.timestamp.isoformat() if result.timestamp else None,
            "dimension_scores": result.dimension_scores,
            "evaluator_version": result.evaluator_version
        }
    
    def _export_to_csv(self, results: List[EvaluationResult], filename: str) -> str:
        """Export results to CSV format."""
        csv_file = self.output_dir / f"{filename}.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if not results:
                return str(csv_file)
            
            # Get all dimension keys
            all_dimensions = set()
            for result in results:
                all_dimensions.update(result.dimension_scores.keys())
            
            fieldnames = [
                'response_id', 'question', 'persona', 'weighted_score', 
                'score_category', 'confidence_score', 'timestamp'
            ] + [f'dim_{dim}' for dim in sorted(all_dimensions)]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                row = {
                    'response_id': result.response_id,
                    'question': result.question[:100] + '...' if len(result.question) > 100 else result.question,
                    'persona': result.persona.value,
                    'weighted_score': result.weighted_score,
                    'score_category': result.score_category,
                    'confidence_score': result.confidence_score,
                    'timestamp': result.timestamp.isoformat() if result.timestamp else ''
                }
                
                # Add dimension scores
                for dim in all_dimensions:
                    row[f'dim_{dim}'] = result.dimension_scores.get(dim, '')
                
                writer.writerow(row)
        
        return str(csv_file)
    
    def _export_to_json(self, results: List[EvaluationResult], filename: str) -> str:
        """Export results to JSON format."""
        json_file = self.output_dir / f"{filename}.json"
        
        export_data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "total_results": len(results),
                "export_version": "1.0.0"
            },
            "evaluations": [self._format_evaluation_for_export(result) for result in results]
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return str(json_file)
    
    def _generate_html_report(self, report_data: Dict[str, Any], report_name: str):
        """Generate HTML version of the report."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report_data['metadata']['report_name']} - FACT Evaluation Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .score {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                .insight {{ background-color: #e9ecef; padding: 10px; margin: 5px 0; border-radius: 3px; }}
                .recommendation {{ background-color: #fff3cd; padding: 15px; margin: 10px 0; border-left: 4px solid #ffc107; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>FACT System Evaluation Report</h1>
                <p>Generated: {report_data['metadata']['generated_at']}</p>
                <p>Total Evaluations: {report_data['metadata']['total_evaluations']}</p>
            </div>
            
            <h2>Executive Summary</h2>
            <div class="metric">
                <div class="score">{report_data['executive_summary']['average_score']:.1f}/100</div>
                <div>Overall Score</div>
            </div>
            <div class="metric">
                <div class="score">{report_data['executive_summary']['confidence_level']:.1%}</div>
                <div>Confidence Level</div>
            </div>
            
            <h2>Key Insights</h2>
            {chr(10).join([f'<div class="insight">{insight}</div>' for insight in report_data['quality_insights']])}
            
            <h2>Recommendations</h2>
            {chr(10).join([f'<div class="recommendation"><strong>{rec["category"]}</strong>: {rec["recommendation"]}</div>' for rec in report_data['recommendations']])}
        </body>
        </html>
        """
        
        html_file = self.output_dir / f"{report_name}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_csv_export(self, results: List[EvaluationResult], report_name: str):
        """Generate CSV export alongside the report."""
        self._export_to_csv(results, f"{report_name}_data")

# Global reporter instance
EVALUATION_REPORTER = EvaluationReporter()
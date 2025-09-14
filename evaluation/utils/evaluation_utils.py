"""
Utility functions for FACT System Response Evaluation
Helper functions and tools for evaluation framework.
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from pathlib import Path
import logging

from ..config.scoring_rubric import PersonaType, ScoreDimension
from ..core.response_evaluator import EvaluationResult, EvaluationCriteria

class EvaluationUtils:
    """Utility functions for response evaluation."""
    
    @staticmethod
    def load_evaluation_data(file_path: str) -> List[EvaluationResult]:
        """
        Load evaluation results from a JSON file.
        
        Args:
            file_path: Path to the evaluation data file
            
        Returns:
            List of EvaluationResult objects
        """
        results = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'evaluations' in data:
                evaluations_data = data['evaluations']
            elif isinstance(data, list):
                evaluations_data = data
            else:
                raise ValueError("Invalid data format")
            
            for eval_data in evaluations_data:
                result = EvaluationResult(
                    response_id=eval_data['response_id'],
                    question=eval_data['question'],
                    response=eval_data['response'],
                    persona=PersonaType(eval_data['persona']),
                    dimension_scores=eval_data['dimension_scores'],
                    weighted_score=eval_data['weighted_score'],
                    score_category=eval_data['score_category'],
                    score_description=eval_data.get('score_description', ''),
                    evaluation_details=eval_data.get('evaluation_details', {}),
                    confidence_score=eval_data['confidence_score'],
                    timestamp=datetime.fromisoformat(eval_data['timestamp']) if eval_data.get('timestamp') else datetime.now(),
                    evaluator_version=eval_data.get('evaluator_version', '1.0.0')
                )
                results.append(result)
        
        except Exception as e:
            logging.error(f"Error loading evaluation data from {file_path}: {e}")
            raise
        
        return results
    
    @staticmethod
    def save_evaluation_data(
        results: List[EvaluationResult],
        file_path: str,
        include_metadata: bool = True
    ) -> None:
        """
        Save evaluation results to a JSON file.
        
        Args:
            results: List of evaluation results
            file_path: Path to save the data
            include_metadata: Whether to include metadata
        """
        data = {
            "evaluations": [EvaluationUtils._serialize_result(result) for result in results]
        }
        
        if include_metadata:
            data["metadata"] = {
                "saved_at": datetime.now().isoformat(),
                "total_results": len(results),
                "version": "1.0.0"
            }
        
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        
        except Exception as e:
            logging.error(f"Error saving evaluation data to {file_path}: {e}")
            raise
    
    @staticmethod
    def _serialize_result(result: EvaluationResult) -> Dict[str, Any]:
        """Serialize an EvaluationResult to dictionary."""
        return {
            "response_id": result.response_id,
            "question": result.question,
            "response": result.response,
            "persona": result.persona.value,
            "dimension_scores": result.dimension_scores,
            "weighted_score": result.weighted_score,
            "score_category": result.score_category,
            "score_description": result.score_description,
            "evaluation_details": result.evaluation_details,
            "confidence_score": result.confidence_score,
            "timestamp": result.timestamp.isoformat() if result.timestamp else None,
            "evaluator_version": result.evaluator_version
        }
    
    @staticmethod
    def filter_results_by_criteria(
        results: List[EvaluationResult],
        criteria: Dict[str, Any]
    ) -> List[EvaluationResult]:
        """
        Filter evaluation results by various criteria.
        
        Args:
            results: List of evaluation results
            criteria: Filter criteria dictionary
            
        Returns:
            Filtered list of results
        """
        filtered = results.copy()
        
        # Filter by persona
        if 'persona' in criteria:
            persona_filter = criteria['persona']
            if isinstance(persona_filter, str):
                persona_filter = PersonaType(persona_filter)
            filtered = [r for r in filtered if r.persona == persona_filter]
        
        # Filter by score range
        if 'min_score' in criteria:
            min_score = criteria['min_score']
            filtered = [r for r in filtered if r.weighted_score >= min_score]
        
        if 'max_score' in criteria:
            max_score = criteria['max_score']
            filtered = [r for r in filtered if r.weighted_score <= max_score]
        
        # Filter by date range
        if 'start_date' in criteria:
            start_date = criteria['start_date']
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date)
            filtered = [r for r in filtered if r.timestamp and r.timestamp >= start_date]
        
        if 'end_date' in criteria:
            end_date = criteria['end_date']
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)
            filtered = [r for r in filtered if r.timestamp and r.timestamp <= end_date]
        
        # Filter by confidence level
        if 'min_confidence' in criteria:
            min_confidence = criteria['min_confidence']
            filtered = [r for r in filtered if r.confidence_score >= min_confidence]
        
        # Filter by score category
        if 'score_category' in criteria:
            category = criteria['score_category']
            filtered = [r for r in filtered if r.score_category == category]
        
        return filtered
    
    @staticmethod
    def calculate_improvement_potential(
        results: List[EvaluationResult],
        target_score: float = 85.0
    ) -> Dict[str, Any]:
        """
        Calculate improvement potential for different dimensions.
        
        Args:
            results: List of evaluation results
            target_score: Target score to achieve
            
        Returns:
            Dictionary with improvement analysis
        """
        if not results:
            return {}
        
        # Calculate current dimension averages
        dimension_totals = {}
        dimension_counts = {}
        
        for result in results:
            for dim, score in result.dimension_scores.items():
                if dim not in dimension_totals:
                    dimension_totals[dim] = 0
                    dimension_counts[dim] = 0
                dimension_totals[dim] += score
                dimension_counts[dim] += 1
        
        dimension_averages = {
            dim: dimension_totals[dim] / dimension_counts[dim]
            for dim in dimension_totals
        }
        
        # Calculate improvement potential
        improvement_potential = {}
        total_gap = 0
        
        for dim, current_score in dimension_averages.items():
            if current_score < target_score:
                gap = target_score - current_score
                improvement_potential[dim] = {
                    "current_score": current_score,
                    "target_score": target_score,
                    "improvement_needed": gap,
                    "priority": "high" if gap > 20 else "medium" if gap > 10 else "low"
                }
                total_gap += gap
        
        return {
            "dimension_improvement": improvement_potential,
            "total_improvement_needed": total_gap,
            "dimensions_at_target": [
                dim for dim, score in dimension_averages.items()
                if score >= target_score
            ],
            "highest_priority_dimension": min(
                dimension_averages.items(), key=lambda x: x[1]
            )[0] if dimension_averages else None
        }
    
    @staticmethod
    def generate_persona_recommendations(
        results: List[EvaluationResult]
    ) -> Dict[str, List[str]]:
        """
        Generate persona-specific recommendations based on results.
        
        Args:
            results: List of evaluation results
            
        Returns:
            Dictionary of persona-specific recommendations
        """
        persona_performance = {}
        
        # Group results by persona
        for result in results:
            persona = result.persona.value
            if persona not in persona_performance:
                persona_performance[persona] = {
                    "scores": [],
                    "dimension_scores": {},
                    "low_scoring_responses": []
                }
            
            persona_performance[persona]["scores"].append(result.weighted_score)
            
            # Track dimension scores
            for dim, score in result.dimension_scores.items():
                if dim not in persona_performance[persona]["dimension_scores"]:
                    persona_performance[persona]["dimension_scores"][dim] = []
                persona_performance[persona]["dimension_scores"][dim].append(score)
            
            # Track low-scoring responses
            if result.weighted_score < 70:
                persona_performance[persona]["low_scoring_responses"].append(result)
        
        # Generate recommendations
        recommendations = {}
        
        for persona, data in persona_performance.items():
            persona_recommendations = []
            
            # Overall performance recommendation
            avg_score = sum(data["scores"]) / len(data["scores"])
            if avg_score < 70:
                persona_recommendations.append(
                    f"Overall {persona} performance is below target ({avg_score:.1f}/100). "
                    "Consider specialized training for this persona type."
                )
            
            # Dimension-specific recommendations
            for dim, scores in data["dimension_scores"].items():
                avg_dim_score = sum(scores) / len(scores)
                if avg_dim_score < 65:
                    persona_recommendations.append(
                        f"Improve {dim.replace('_', ' ')} for {persona} persona. "
                        f"Current average: {avg_dim_score:.1f}/100"
                    )
            
            # Pattern-based recommendations
            if len(data["low_scoring_responses"]) > len(data["scores"]) * 0.3:
                persona_recommendations.append(
                    f"High proportion of low-scoring responses for {persona} persona. "
                    "Review response templates and training materials."
                )
            
            recommendations[persona] = persona_recommendations
        
        return recommendations
    
    @staticmethod
    def extract_common_issues(
        results: List[EvaluationResult],
        min_frequency: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Extract common issues from evaluation details.
        
        Args:
            results: List of evaluation results
            min_frequency: Minimum frequency for an issue to be considered common
            
        Returns:
            List of common issues with frequency
        """
        issue_patterns = {}
        
        for result in results:
            for dim, details in result.evaluation_details.items():
                if "factors" in details:
                    for factor in details["factors"]:
                        # Extract patterns from factors
                        pattern = EvaluationUtils._normalize_issue_pattern(factor)
                        if pattern not in issue_patterns:
                            issue_patterns[pattern] = {
                                "count": 0,
                                "dimension": dim,
                                "examples": []
                            }
                        issue_patterns[pattern]["count"] += 1
                        if len(issue_patterns[pattern]["examples"]) < 3:
                            issue_patterns[pattern]["examples"].append({
                                "response_id": result.response_id,
                                "factor": factor
                            })
        
        # Filter by minimum frequency
        common_issues = [
            {
                "pattern": pattern,
                "frequency": data["count"],
                "dimension": data["dimension"],
                "examples": data["examples"]
            }
            for pattern, data in issue_patterns.items()
            if data["count"] >= min_frequency
        ]
        
        # Sort by frequency
        common_issues.sort(key=lambda x: x["frequency"], reverse=True)
        
        return common_issues
    
    @staticmethod
    def _normalize_issue_pattern(factor: str) -> str:
        """Normalize issue pattern for grouping."""
        # Simple pattern extraction - could be enhanced with NLP
        factor = factor.lower()
        
        # Common pattern normalizations
        patterns = {
            r".*lack.*completeness.*": "completeness_issues",
            r".*short.*response.*": "length_issues", 
            r".*missing.*element.*": "missing_elements",
            r".*unclear.*": "clarity_issues",
            r".*not.*relevant.*": "relevance_issues",
            r".*persona.*mismatch.*": "persona_alignment_issues"
        }
        
        for pattern_regex, normalized_pattern in patterns.items():
            if re.match(pattern_regex, factor):
                return normalized_pattern
        
        return factor[:50] + "..." if len(factor) > 50 else factor
    
    @staticmethod
    def calculate_statistical_significance(
        group1_scores: List[float],
        group2_scores: List[float],
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Calculate statistical significance between two groups of scores.
        
        Args:
            group1_scores: First group of scores
            group2_scores: Second group of scores  
            confidence_level: Confidence level for significance testing
            
        Returns:
            Statistical analysis results
        """
        try:
            import scipy.stats as stats
        except ImportError:
            return {
                "error": "scipy not available for statistical analysis",
                "significant": False
            }
        
        if len(group1_scores) < 2 or len(group2_scores) < 2:
            return {
                "error": "Insufficient data for statistical analysis",
                "significant": False
            }
        
        # Perform t-test
        t_stat, p_value = stats.ttest_ind(group1_scores, group2_scores)
        
        # Calculate effect size (Cohen's d)
        mean1, mean2 = sum(group1_scores) / len(group1_scores), sum(group2_scores) / len(group2_scores)
        pooled_std = (
            ((len(group1_scores) - 1) * (sum((x - mean1) ** 2 for x in group1_scores) / (len(group1_scores) - 1)) +
             (len(group2_scores) - 1) * (sum((x - mean2) ** 2 for x in group2_scores) / (len(group2_scores) - 1))) /
            (len(group1_scores) + len(group2_scores) - 2)
        ) ** 0.5
        
        cohens_d = (mean1 - mean2) / pooled_std if pooled_std > 0 else 0
        
        alpha = 1 - confidence_level
        significant = p_value < alpha
        
        return {
            "t_statistic": t_stat,
            "p_value": p_value,
            "significant": significant,
            "confidence_level": confidence_level,
            "effect_size": cohens_d,
            "group1_mean": mean1,
            "group2_mean": mean2,
            "interpretation": EvaluationUtils._interpret_effect_size(cohens_d)
        }
    
    @staticmethod
    def _interpret_effect_size(cohens_d: float) -> str:
        """Interpret Cohen's d effect size."""
        abs_d = abs(cohens_d)
        if abs_d < 0.2:
            return "negligible effect"
        elif abs_d < 0.5:
            return "small effect" 
        elif abs_d < 0.8:
            return "medium effect"
        else:
            return "large effect"

# Global utility instance
EVALUATION_UTILS = EvaluationUtils()
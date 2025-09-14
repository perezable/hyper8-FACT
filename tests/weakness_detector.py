#!/usr/bin/env python3
"""
FACT System Weakness Detection and Pattern Analysis Module

This module identifies systematic weaknesses, failure patterns, knowledge gaps,
and provides targeted recommendations for improvement.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Set
from datetime import datetime
from collections import defaultdict, Counter
import re
import structlog
from dataclasses import dataclass, asdict
from performance_analyzer import AnalyzedResponse, ScoringRubric
from statistical_reporter import StatisticalReporter

logger = structlog.get_logger(__name__)


@dataclass
class WeaknessPlattern:
    """Represents a systematic weakness pattern."""
    pattern_id: str
    pattern_type: str  # "knowledge_gap", "retrieval_failure", "performance_issue", etc.
    description: str
    affected_queries: List[str]
    frequency: int
    severity: float  # 0-1 scale
    impact_metrics: Dict[str, float]
    root_causes: List[str]
    recommended_fixes: List[str]
    priority: str  # "critical", "high", "medium", "low"


@dataclass  
class KnowledgeGap:
    """Represents a gap in the knowledge base."""
    gap_id: str
    topic_area: str
    category: str
    state: Optional[str]
    missing_content_type: str  # "specific_requirement", "procedure", "regulation", etc.
    evidence_queries: List[str]
    user_impact: float  # How many users affected
    business_impact: str  # "high", "medium", "low"
    suggested_content: List[str]
    data_sources: List[str]


@dataclass
class FailurePattern:
    """Represents a systematic failure pattern."""
    pattern_id: str
    failure_type: str  # "semantic_mismatch", "category_confusion", "state_specificity", etc.
    trigger_conditions: Dict[str, Any]
    failure_rate: float
    affected_personas: List[str]
    example_failures: List[Dict[str, Any]]
    mitigation_strategies: List[str]


@dataclass
class PersonaGap:
    """Represents persona-specific performance gaps."""
    persona_name: str
    weak_categories: List[str]
    missed_queries: List[str]
    avg_performance_gap: float  # vs. best persona
    specific_issues: List[str]
    training_needs: List[str]
    content_adaptations: List[str]


@dataclass
class StateGap:
    """Represents state-specific coverage gaps."""
    state_code: str
    coverage_completeness: float  # 0-1
    missing_categories: List[str]
    outdated_content: List[str]
    regulation_gaps: List[str]
    priority_additions: List[str]
    source_verification_needed: List[str]


class WeaknessDetector:
    """Advanced system for detecting and analyzing weaknesses in FACT performance."""
    
    def __init__(self):
        """Initialize the weakness detector."""
        self.analyzed_responses: List[AnalyzedResponse] = []
        self.weakness_patterns: List[WeaknessPlattern] = []
        self.knowledge_gaps: List[KnowledgeGap] = []
        self.failure_patterns: List[FailurePattern] = []
        self.persona_gaps: List[PersonaGap] = []
        self.state_gaps: List[StateGap] = []
        
        # Thresholds for detection
        self.thresholds = {
            'critical_failure_rate': 0.8,    # 80% failure rate = critical
            'high_failure_rate': 0.6,        # 60% failure rate = high priority
            'min_pattern_frequency': 3,       # Need 3+ occurrences to identify pattern
            'low_coverage_threshold': 0.3,    # <30% coverage = gap
            'performance_gap_threshold': 0.2  # 20% performance gap = significant
        }
    
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
        logger.info(f"Loaded {len(analyzed_responses)} analyzed responses for weakness detection")
    
    def detect_systematic_weaknesses(self) -> List[WeaknessPlattern]:
        """Detect systematic weakness patterns across all responses."""
        df = self._to_dataframe()
        patterns = []
        
        # Pattern 1: Query variation handling failures
        variation_failures = self._detect_variation_handling_failures(df)
        patterns.extend(variation_failures)
        
        # Pattern 2: Category confusion patterns
        category_confusion = self._detect_category_confusion_patterns(df)
        patterns.extend(category_confusion)
        
        # Pattern 3: State specificity failures
        state_failures = self._detect_state_specificity_failures(df)
        patterns.extend(state_failures)
        
        # Pattern 4: Performance degradation patterns
        performance_issues = self._detect_performance_degradation_patterns(df)
        patterns.extend(performance_issues)
        
        # Pattern 5: Semantic retrieval failures
        semantic_failures = self._detect_semantic_retrieval_failures(df)
        patterns.extend(semantic_failures)
        
        # Pattern 6: Confidence/accuracy misalignment
        confidence_misalignment = self._detect_confidence_misalignment_patterns(df)
        patterns.extend(confidence_misalignment)
        
        self.weakness_patterns = patterns
        return patterns
    
    def _detect_variation_handling_failures(self, df: pd.DataFrame) -> List[WeaknessPlattern]:
        """Detect failures in handling query variations."""
        patterns = []
        
        # Group by original question and analyze variation performance
        question_groups = df.groupby('original_question')
        
        for question, group_data in question_groups:
            if len(group_data) < 2:  # Need multiple variations
                continue
            
            # Check for high variation in scores
            score_std = group_data['overall_score'].std()
            if score_std > 0.3:  # High variation in performance
                failed_variations = group_data[group_data['overall_score'] < 0.5]
                
                if len(failed_variations) >= 2:
                    patterns.append(WeaknessPlattern(
                        pattern_id=f"variation_handling_{hash(question) % 10000}",
                        pattern_type="variation_handling_failure",
                        description=f"Inconsistent performance across query variations for: {question[:100]}...",
                        affected_queries=[question],
                        frequency=len(failed_variations),
                        severity=score_std,
                        impact_metrics={
                            "variation_failure_rate": len(failed_variations) / len(group_data),
                            "score_variance": float(score_std)
                        },
                        root_causes=[
                            "Query preprocessing inconsistencies",
                            "Insufficient variation training data",
                            "Keyword dependency in retrieval"
                        ],
                        recommended_fixes=[
                            "Improve query normalization",
                            "Add more training variations",
                            "Implement semantic search improvements"
                        ],
                        priority="high" if score_std > 0.5 else "medium"
                    ))
        
        return patterns
    
    def _detect_category_confusion_patterns(self, df: pd.DataFrame) -> List[WeaknessPlattern]:
        """Detect systematic category classification failures."""
        patterns = []
        
        # Find queries with low category accuracy but high semantic similarity
        confused_responses = df[
            (df['category_accuracy'] < 0.5) & 
            (df['semantic_similarity'] > 0.7)
        ]
        
        if len(confused_responses) >= self.thresholds['min_pattern_frequency']:
            # Analyze confusion patterns
            confusion_matrix = defaultdict(int)
            for _, row in confused_responses.iterrows():
                # This would ideally compare expected vs retrieved category
                # For now, we'll identify commonly confused categories
                confusion_matrix[row['category']] += 1
            
            most_confused = max(confusion_matrix.items(), key=lambda x: x[1])
            
            patterns.append(WeaknessPlattern(
                pattern_id="category_confusion_primary",
                pattern_type="category_confusion",
                description=f"High category confusion rate, especially in '{most_confused[0]}' category",
                affected_queries=confused_responses['test_id'].tolist(),
                frequency=len(confused_responses),
                severity=1.0 - confused_responses['category_accuracy'].mean(),
                impact_metrics={
                    "confusion_rate": len(confused_responses) / len(df),
                    "most_affected_category": most_confused[0],
                    "confusion_frequency": most_confused[1]
                },
                root_causes=[
                    "Overlapping category definitions",
                    "Insufficient category training data",
                    "Ambiguous query classification"
                ],
                recommended_fixes=[
                    "Refine category taxonomy",
                    "Add category-specific training data",
                    "Implement hierarchical classification"
                ],
                priority="high"
            ))
        
        return patterns
    
    def _detect_state_specificity_failures(self, df: pd.DataFrame) -> List[WeaknessPlattern]:
        """Detect failures in state-specific information retrieval."""
        patterns = []
        
        # Find responses with low state relevance
        state_failures = df[
            (df['state_relevance'] < 0.5) & 
            (df['state'].notna()) & 
            (df['state'] != '')
        ]
        
        if len(state_failures) >= self.thresholds['min_pattern_frequency']:
            # Group by state to find patterns
            state_failure_counts = state_failures['state'].value_counts()
            
            for state, count in state_failure_counts.head(5).items():
                state_data = state_failures[state_failures['state'] == state]
                
                patterns.append(WeaknessPlattern(
                    pattern_id=f"state_specificity_{state}",
                    pattern_type="state_specificity_failure", 
                    description=f"Poor state-specific information retrieval for {state}",
                    affected_queries=state_data['test_id'].tolist(),
                    frequency=count,
                    severity=1.0 - state_data['state_relevance'].mean(),
                    impact_metrics={
                        "state_failure_rate": count / len(df[df['state'] == state]),
                        "avg_state_relevance": float(state_data['state_relevance'].mean())
                    },
                    root_causes=[
                        f"Insufficient {state}-specific content",
                        "Generic responses overriding state-specific ones",
                        "Poor state entity recognition"
                    ],
                    recommended_fixes=[
                        f"Add comprehensive {state} regulations and requirements",
                        "Improve state-specific content tagging",
                        "Implement state-aware retrieval ranking"
                    ],
                    priority="high" if count > 10 else "medium"
                ))
        
        return patterns
    
    def _detect_performance_degradation_patterns(self, df: pd.DataFrame) -> List[WeaknessPlattern]:
        """Detect systematic performance issues."""
        patterns = []
        
        # Identify slow response patterns
        slow_responses = df[df['response_time_ms'] > 1000]  # >1 second
        
        if len(slow_responses) > len(df) * 0.1:  # >10% slow responses
            # Analyze what causes slow responses
            slow_categories = slow_responses['category'].value_counts().head(3)
            slow_personas = slow_responses['persona'].value_counts().head(3)
            
            patterns.append(WeaknessPlattern(
                pattern_id="performance_degradation_response_time",
                pattern_type="performance_issue",
                description="Systematic response time degradation affecting user experience",
                affected_queries=slow_responses['test_id'].tolist()[:20],  # Sample
                frequency=len(slow_responses),
                severity=slow_responses['response_time_ms'].mean() / 1000.0,  # Convert to severity
                impact_metrics={
                    "slow_response_rate": len(slow_responses) / len(df),
                    "avg_slow_time": float(slow_responses['response_time_ms'].mean()),
                    "affected_categories": slow_categories.to_dict(),
                    "affected_personas": slow_personas.to_dict()
                },
                root_causes=[
                    "Database query optimization issues",
                    "Complex retrieval algorithms",
                    "Resource contention"
                ],
                recommended_fixes=[
                    "Optimize database indexing",
                    "Implement response caching",
                    "Add performance monitoring alerts"
                ],
                priority="high"
            ))
        
        return patterns
    
    def _detect_semantic_retrieval_failures(self, df: pd.DataFrame) -> List[WeaknessPlattern]:
        """Detect semantic search and retrieval failures."""
        patterns = []
        
        # Find cases where we have no results but should have found something
        no_result_cases = df[
            (df['match_type'] == 'none') & 
            (df['retrieved_answer'] == '')
        ]
        
        if len(no_result_cases) >= self.thresholds['min_pattern_frequency']:
            # Analyze common characteristics of failed retrievals
            failed_categories = no_result_cases['category'].value_counts()
            failed_personas = no_result_cases['persona'].value_counts()
            
            patterns.append(WeaknessPlattern(
                pattern_id="semantic_retrieval_complete_failure",
                pattern_type="retrieval_failure",
                description="Complete retrieval failures - queries returning no results",
                affected_queries=no_result_cases['test_id'].tolist(),
                frequency=len(no_result_cases),
                severity=len(no_result_cases) / len(df),
                impact_metrics={
                    "no_result_rate": len(no_result_cases) / len(df),
                    "failed_categories": failed_categories.head(5).to_dict(),
                    "failed_personas": failed_personas.head(5).to_dict()
                },
                root_causes=[
                    "Knowledge base coverage gaps",
                    "Query preprocessing failures", 
                    "Search index issues"
                ],
                recommended_fixes=[
                    "Add missing content to knowledge base",
                    "Improve query preprocessing pipeline",
                    "Implement fallback search strategies"
                ],
                priority="critical"
            ))
        
        # Find cases with poor semantic similarity despite retrieving something
        poor_semantic = df[
            (df['retrieved_answer'] != '') & 
            (df['semantic_similarity'] < 0.3)
        ]
        
        if len(poor_semantic) >= self.thresholds['min_pattern_frequency']:
            patterns.append(WeaknessPlattern(
                pattern_id="semantic_retrieval_poor_matching",
                pattern_type="semantic_failure",
                description="Poor semantic matching - retrieving irrelevant content",
                affected_queries=poor_semantic['test_id'].tolist()[:20],
                frequency=len(poor_semantic),
                severity=1.0 - poor_semantic['semantic_similarity'].mean(),
                impact_metrics={
                    "poor_semantic_rate": len(poor_semantic) / len(df),
                    "avg_semantic_score": float(poor_semantic['semantic_similarity'].mean())
                },
                root_causes=[
                    "Inadequate semantic embeddings",
                    "Poor query-document matching",
                    "Insufficient context understanding"
                ],
                recommended_fixes=[
                    "Upgrade to better embedding models",
                    "Implement re-ranking algorithms",
                    "Add contextual query expansion"
                ],
                priority="high"
            ))
        
        return patterns
    
    def _detect_confidence_misalignment_patterns(self, df: pd.DataFrame) -> List[WeaknessPlattern]:
        """Detect misalignment between system confidence and actual performance."""
        patterns = []
        
        # Find high confidence but low performance cases
        overconfident = df[
            (df['system_confidence'] > 0.8) & 
            (df['overall_score'] < 0.5)
        ]
        
        if len(overconfident) >= self.thresholds['min_pattern_frequency']:
            patterns.append(WeaknessPlattern(
                pattern_id="confidence_overconfidence",
                pattern_type="confidence_misalignment",
                description="System overconfidence - high confidence but poor actual performance",
                affected_queries=overconfident['test_id'].tolist(),
                frequency=len(overconfident),
                severity=overconfident['system_confidence'].mean() - overconfident['overall_score'].mean(),
                impact_metrics={
                    "overconfident_rate": len(overconfident) / len(df),
                    "confidence_performance_gap": float(
                        overconfident['system_confidence'].mean() - overconfident['overall_score'].mean()
                    )
                },
                root_causes=[
                    "Poorly calibrated confidence estimation",
                    "Training-inference distribution mismatch",
                    "Overemphasis on keyword matches"
                ],
                recommended_fixes=[
                    "Recalibrate confidence scoring algorithm",
                    "Add uncertainty quantification",
                    "Implement confidence validation testing"
                ],
                priority="medium"
            ))
        
        # Find low confidence but high performance cases
        underconfident = df[
            (df['system_confidence'] < 0.5) & 
            (df['overall_score'] > 0.8)
        ]
        
        if len(underconfident) >= self.thresholds['min_pattern_frequency']:
            patterns.append(WeaknessPlattern(
                pattern_id="confidence_underconfidence",
                pattern_type="confidence_misalignment",
                description="System underconfidence - low confidence but good actual performance",
                affected_queries=underconfident['test_id'].tolist(),
                frequency=len(underconfident),
                severity=underconfident['overall_score'].mean() - underconfident['system_confidence'].mean(),
                impact_metrics={
                    "underconfident_rate": len(underconfident) / len(df),
                    "missed_good_responses": len(underconfident)
                },
                root_causes=[
                    "Conservative confidence thresholds",
                    "Incomplete confidence feature set",
                    "Bias towards exact matches"
                ],
                recommended_fixes=[
                    "Tune confidence thresholds",
                    "Add semantic similarity to confidence calculation",
                    "Implement multi-factor confidence scoring"
                ],
                priority="low"
            ))
        
        return patterns
    
    def identify_knowledge_gaps(self) -> List[KnowledgeGap]:
        """Identify systematic knowledge gaps in the content base."""
        df = self._to_dataframe()
        gaps = []
        
        # Gap 1: No result queries indicate missing content
        no_result_queries = df[df['match_type'] == 'none']
        
        if len(no_result_queries) > 0:
            # Group by category and state to identify gap patterns
            gap_patterns = no_result_queries.groupby(['category', 'state']).size()
            
            for (category, state), count in gap_patterns.items():
                if count >= 3:  # Significant gap
                    evidence_queries = no_result_queries[
                        (no_result_queries['category'] == category) & 
                        (no_result_queries['state'] == state)
                    ]['original_question'].tolist()
                    
                    gaps.append(KnowledgeGap(
                        gap_id=f"content_gap_{category}_{state}",
                        topic_area=category or "general",
                        category=category or "unknown",
                        state=state if state else None,
                        missing_content_type="specific_requirements",
                        evidence_queries=evidence_queries[:5],  # Sample
                        user_impact=count / len(df),
                        business_impact="high" if count > 10 else "medium",
                        suggested_content=[
                            f"Add comprehensive {category} information for {state}" if state else f"Add general {category} content",
                            f"Include specific requirements and procedures",
                            f"Add regulatory updates and compliance information"
                        ],
                        data_sources=[
                            f"Official {state} insurance department" if state else "NAIC guidelines",
                            "Regulatory databases",
                            "Professional association resources"
                        ]
                    ))
        
        # Gap 2: Low semantic similarity suggests content quality gaps
        poor_content_matches = df[
            (df['retrieved_answer'] != '') & 
            (df['semantic_similarity'] < 0.4)
        ]
        
        if len(poor_content_matches) > 0:
            content_categories = poor_content_matches['category'].value_counts()
            
            for category, count in content_categories.head(5).items():
                if count >= 5:
                    category_data = poor_content_matches[poor_content_matches['category'] == category]
                    
                    gaps.append(KnowledgeGap(
                        gap_id=f"quality_gap_{category}",
                        topic_area=category,
                        category=category,
                        state=None,
                        missing_content_type="detailed_explanations",
                        evidence_queries=category_data['original_question'].tolist()[:3],
                        user_impact=count / len(df),
                        business_impact="medium",
                        suggested_content=[
                            f"Improve {category} content quality and detail",
                            "Add examples and practical guidance",
                            "Include step-by-step procedures"
                        ],
                        data_sources=[
                            "Subject matter expert review",
                            "User feedback analysis", 
                            "Best practice documentation"
                        ]
                    ))
        
        self.knowledge_gaps = gaps
        return gaps
    
    def analyze_persona_gaps(self) -> List[PersonaGap]:
        """Analyze performance gaps by persona."""
        df = self._to_dataframe()
        gaps = []
        
        # Calculate overall average performance
        overall_avg = df['overall_score'].mean()
        
        for persona in df['persona'].unique():
            if not persona:
                continue
                
            persona_data = df[df['persona'] == persona]
            persona_avg = persona_data['overall_score'].mean()
            
            # Only consider significant gaps
            if overall_avg - persona_avg > self.thresholds['performance_gap_threshold']:
                # Find weak categories for this persona
                category_performance = persona_data.groupby('category')['overall_score'].mean()
                weak_categories = category_performance[category_performance < 0.6].index.tolist()
                
                # Find commonly missed queries
                missed_queries = persona_data[persona_data['overall_score'] < 0.5]
                common_misses = missed_queries['original_question'].tolist()[:5]
                
                # Identify specific issues
                specific_issues = []
                if persona_data['semantic_similarity'].mean() < 0.6:
                    specific_issues.append("Poor semantic understanding")
                if persona_data['response_time_ms'].mean() > 500:
                    specific_issues.append("Slow response times")
                if persona_data['category_accuracy'].mean() < 0.7:
                    specific_issues.append("Category classification issues")
                
                gaps.append(PersonaGap(
                    persona_name=persona,
                    weak_categories=weak_categories,
                    missed_queries=common_misses,
                    avg_performance_gap=overall_avg - persona_avg,
                    specific_issues=specific_issues,
                    training_needs=[
                        f"Improve {persona} query handling",
                        f"Add {persona}-specific training data",
                        "Optimize retrieval for persona patterns"
                    ],
                    content_adaptations=[
                        f"Create {persona}-focused content format",
                        "Add persona-relevant examples",
                        "Adjust complexity for persona expertise level"
                    ]
                ))
        
        self.persona_gaps = gaps
        return gaps
    
    def analyze_state_gaps(self) -> List[StateGap]:
        """Analyze state-specific coverage and performance gaps."""
        df = self._to_dataframe()
        gaps = []
        
        # Analyze each state
        for state in df['state'].unique():
            if not state:
                continue
                
            state_data = df[df['state'] == state]
            total_possible_categories = len(df['category'].unique())
            state_categories = len(state_data['category'].unique())
            
            coverage_completeness = state_categories / total_possible_categories
            
            # Only analyze states with significant coverage gaps
            if coverage_completeness < 0.7:
                # Find missing categories
                all_categories = set(df['category'].unique())
                state_categories_set = set(state_data['category'].unique())
                missing_categories = list(all_categories - state_categories_set)
                
                # Find poorly performing categories
                category_performance = state_data.groupby('category')['overall_score'].mean()
                weak_categories = category_performance[category_performance < 0.5].index.tolist()
                
                # Identify potential outdated content (low confidence scores)
                potential_outdated = state_data[state_data['system_confidence'] < 0.5]
                outdated_indicators = potential_outdated['category'].unique().tolist()
                
                gaps.append(StateGap(
                    state_code=state,
                    coverage_completeness=coverage_completeness,
                    missing_categories=missing_categories[:5],  # Top 5
                    outdated_content=outdated_indicators[:3],   # Top 3 
                    regulation_gaps=[
                        f"{state} continuing education requirements",
                        f"{state} license renewal procedures",
                        f"{state} regulatory updates"
                    ],
                    priority_additions=[
                        f"Complete {state} licensing requirements",
                        f"{state} exam information",
                        f"{state} renewal deadlines and procedures"
                    ],
                    source_verification_needed=[
                        f"Verify current {state} regulations",
                        f"Update {state} fee schedules",
                        f"Confirm {state} continuing education providers"
                    ]
                ))
        
        self.state_gaps = gaps
        return gaps
    
    def identify_top_weakness_priorities(self) -> List[Dict[str, Any]]:
        """Identify the top weakness priorities based on impact and frequency."""
        priorities = []
        
        # Combine all weaknesses and score them
        all_weaknesses = []
        
        # Add weakness patterns
        for pattern in self.weakness_patterns:
            impact_score = pattern.severity * pattern.frequency
            all_weaknesses.append({
                "type": "weakness_pattern",
                "id": pattern.pattern_id,
                "description": pattern.description,
                "impact_score": impact_score,
                "priority": pattern.priority,
                "frequency": pattern.frequency,
                "fixes": pattern.recommended_fixes[:3]
            })
        
        # Add knowledge gaps
        for gap in self.knowledge_gaps:
            impact_score = gap.user_impact * 100  # Scale up
            priority_map = {"high": "critical", "medium": "high", "low": "medium"}
            all_weaknesses.append({
                "type": "knowledge_gap", 
                "id": gap.gap_id,
                "description": f"Knowledge gap in {gap.topic_area}",
                "impact_score": impact_score,
                "priority": priority_map.get(gap.business_impact, "medium"),
                "frequency": len(gap.evidence_queries),
                "fixes": gap.suggested_content[:2]
            })
        
        # Sort by impact score and priority
        priority_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        sorted_weaknesses = sorted(
            all_weaknesses,
            key=lambda x: (priority_weights.get(x["priority"], 0), x["impact_score"]),
            reverse=True
        )
        
        return sorted_weaknesses[:20]  # Top 20 priorities
    
    def _to_dataframe(self) -> pd.DataFrame:
        """Convert analyzed responses to DataFrame for analysis."""
        records = []
        
        for resp in self.analyzed_responses:
            record = {
                'test_id': resp.test_id,
                'persona': resp.persona,
                'category': resp.category,
                'state': resp.state,
                'difficulty': resp.difficulty,
                'original_question': resp.original_question,
                'retrieved_answer': resp.retrieved_answer,
                'response_time_ms': resp.response_time_ms,
                'match_type': resp.match_type,
                'system_confidence': resp.system_confidence,
                'performance_tier': resp.performance_tier,
                
                # Scoring rubric metrics
                'overall_score': resp.scoring_rubric.overall_score,
                'semantic_similarity': resp.scoring_rubric.semantic_similarity,
                'category_accuracy': resp.scoring_rubric.category_accuracy,
                'state_relevance': resp.scoring_rubric.state_relevance,
                'completeness': resp.scoring_rubric.completeness,
                'clarity': resp.scoring_rubric.clarity,
            }
            records.append(record)
        
        return pd.DataFrame(records)
    
    def generate_weakness_report(self) -> Dict[str, Any]:
        """Generate comprehensive weakness analysis report."""
        # Run all analyses
        self.detect_systematic_weaknesses()
        self.identify_knowledge_gaps()
        self.analyze_persona_gaps()
        self.analyze_state_gaps()
        
        # Get top priorities
        top_priorities = self.identify_top_weakness_priorities()
        
        report = {
            "metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "total_responses_analyzed": len(self.analyzed_responses),
                "detector_version": "1.0.0"
            },
            "executive_summary": {
                "total_weakness_patterns": len(self.weakness_patterns),
                "total_knowledge_gaps": len(self.knowledge_gaps),
                "total_persona_gaps": len(self.persona_gaps),
                "total_state_gaps": len(self.state_gaps),
                "critical_issues": len([p for p in top_priorities if p["priority"] == "critical"]),
                "high_priority_issues": len([p for p in top_priorities if p["priority"] == "high"])
            },
            "top_priorities": top_priorities,
            "systematic_weaknesses": [asdict(p) for p in self.weakness_patterns],
            "knowledge_gaps": [asdict(g) for g in self.knowledge_gaps],
            "persona_analysis": [asdict(g) for g in self.persona_gaps],
            "state_analysis": [asdict(g) for g in self.state_gaps],
            "recommendations": {
                "immediate_actions": [
                    item["description"] for item in top_priorities[:5]
                ],
                "content_priorities": [
                    gap.suggested_content[0] for gap in self.knowledge_gaps[:5]
                ],
                "system_improvements": [
                    pattern.recommended_fixes[0] for pattern in self.weakness_patterns[:5]
                ]
            }
        }
        
        return report
    
    def save_weakness_report(self, report: Dict[str, Any], filepath: str):
        """Save weakness analysis report to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Weakness analysis report saved to {filepath}")


async def main():
    """Test the weakness detector."""
    print("Weakness Detector - Demo Mode")
    
    detector = WeaknessDetector()
    
    # In production, this would load real analyzed data
    # For demo, create sample weakness report structure
    sample_report = {
        "metadata": {
            "analysis_timestamp": datetime.now().isoformat(),
            "total_responses_analyzed": 0,
            "detector_version": "1.0.0"
        },
        "executive_summary": {
            "total_weakness_patterns": 0,
            "total_knowledge_gaps": 0,
            "total_persona_gaps": 0,
            "total_state_gaps": 0,
            "critical_issues": 0,
            "high_priority_issues": 0
        },
        "top_priorities": [],
        "systematic_weaknesses": [],
        "knowledge_gaps": [],
        "persona_analysis": [],
        "state_analysis": [],
        "recommendations": {
            "immediate_actions": ["Demo mode - no real analysis performed"],
            "content_priorities": ["Load actual test data to generate real recommendations"],
            "system_improvements": ["Implement full weakness detection pipeline"]
        }
    }
    
    # Save demo report
    detector.save_weakness_report(sample_report, 'tests/weakness_analysis_demo.json')
    print("📝 Demo weakness analysis saved to tests/weakness_analysis_demo.json")
    print("💡 Load real analyzed data with load_analyzed_data() to generate actual insights")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
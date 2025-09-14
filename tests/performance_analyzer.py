#!/usr/bin/env python3
"""
FACT System Performance Analysis Engine

This module provides comprehensive analysis of FACT responses using a multi-dimensional 
scoring rubric to evaluate accuracy, relevance, completeness, and performance metrics.
"""

import asyncio
import json
import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import numpy as np
from dataclasses import dataclass, asdict
import structlog
from collections import defaultdict
import sqlite3

# Add src to Python path
script_dir = Path(__file__).parent
src_dir = script_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from db.connection import DatabaseManager
from retrieval.enhanced_search import EnhancedRetriever
from core.errors import DatabaseError

logger = structlog.get_logger(__name__)


@dataclass
class ScoringRubric:
    """Multi-dimensional scoring rubric for FACT responses."""
    # Accuracy dimensions (0-1 scale)
    exact_match: float = 0.0           # Exact ID/content match
    semantic_similarity: float = 0.0   # Semantic similarity score
    category_accuracy: float = 0.0     # Category classification accuracy
    state_relevance: float = 0.0       # State-specific information accuracy
    
    # Quality dimensions (0-1 scale)  
    completeness: float = 0.0          # Response completeness
    relevance: float = 0.0             # Query relevance
    clarity: float = 0.0               # Response clarity and readability
    authority: float = 0.0             # Information authority/reliability
    
    # Performance dimensions
    response_time_score: float = 0.0   # Response time performance (0-1)
    confidence_score: float = 0.0      # System confidence in response
    
    # Meta scoring
    overall_score: float = 0.0         # Weighted overall score
    grade_letter: str = "F"            # Letter grade (A-F)
    
    def calculate_overall_score(self, weights: Dict[str, float] = None) -> float:
        """Calculate weighted overall score."""
        if weights is None:
            weights = {
                'accuracy': 0.4,      # 40% - most important
                'quality': 0.35,      # 35% - content quality
                'performance': 0.25   # 25% - system performance
            }
        
        accuracy_avg = (self.exact_match + self.semantic_similarity + 
                       self.category_accuracy + self.state_relevance) / 4
        
        quality_avg = (self.completeness + self.relevance + 
                      self.clarity + self.authority) / 4
        
        performance_avg = (self.response_time_score + self.confidence_score) / 2
        
        overall = (accuracy_avg * weights['accuracy'] + 
                  quality_avg * weights['quality'] + 
                  performance_avg * weights['performance'])
        
        self.overall_score = overall
        self.grade_letter = self._calculate_grade(overall)
        return overall
    
    def _calculate_grade(self, score: float) -> str:
        """Convert score to letter grade."""
        if score >= 0.95: return "A+"
        elif score >= 0.90: return "A"
        elif score >= 0.85: return "B+"
        elif score >= 0.80: return "B"
        elif score >= 0.75: return "C+"
        elif score >= 0.70: return "C"
        elif score >= 0.60: return "D"
        else: return "F"


@dataclass
class AnalyzedResponse:
    """Represents a fully analyzed FACT response."""
    # Test metadata
    test_id: str
    timestamp: datetime
    persona: str
    category: str
    state: str
    difficulty: str
    
    # Query information
    original_question: str
    query_variation: str
    expected_answer: str
    
    # Response data
    retrieved_answer: str
    response_time_ms: float
    match_type: str
    system_confidence: float
    
    # Analysis results
    scoring_rubric: ScoringRubric
    failure_reasons: List[str]
    improvement_suggestions: List[str]
    
    # Performance classification
    performance_tier: str  # "excellent", "good", "needs_improvement", "poor"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['scoring_rubric'] = asdict(self.scoring_rubric)
        result['timestamp'] = self.timestamp.isoformat()
        return result


class ResponseAnalysisEngine:
    """Core engine for analyzing FACT responses with comprehensive scoring."""
    
    def __init__(self, database_path: str = "data/fact_system.db"):
        """Initialize the analysis engine."""
        self.db_manager = DatabaseManager(database_path)
        self.retriever = EnhancedRetriever(self.db_manager)
        self.analyzed_responses: List[AnalyzedResponse] = []
        
        # Performance thresholds
        self.thresholds = {
            'excellent_response_time': 50,    # ms
            'good_response_time': 200,        # ms
            'poor_response_time': 1000,       # ms
            'min_confidence': 0.8,
            'min_semantic_similarity': 0.7,
            'min_completeness': 0.6
        }
    
    async def initialize(self):
        """Initialize the retriever and load knowledge base metadata."""
        await self.retriever.initialize()
        logger.info("Response analysis engine initialized")
    
    def calculate_semantic_similarity(self, expected: str, retrieved: str) -> float:
        """Calculate semantic similarity between expected and retrieved answers."""
        if not expected or not retrieved:
            return 0.0
        
        expected_lower = expected.lower()
        retrieved_lower = retrieved.lower()
        
        # Exact match bonus
        if expected_lower == retrieved_lower:
            return 1.0
        
        # Tokenize and compare
        expected_tokens = set(re.findall(r'\w+', expected_lower))
        retrieved_tokens = set(re.findall(r'\w+', retrieved_lower))
        
        if not expected_tokens or not retrieved_tokens:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = expected_tokens.intersection(retrieved_tokens)
        union = expected_tokens.union(retrieved_tokens)
        jaccard = len(intersection) / len(union) if union else 0.0
        
        # Bonus for key phrase matches
        key_phrases = self._extract_key_phrases(expected)
        phrase_matches = sum(1 for phrase in key_phrases if phrase.lower() in retrieved_lower)
        phrase_bonus = min(0.3, phrase_matches * 0.1) if key_phrases else 0.0
        
        return min(1.0, jaccard + phrase_bonus)
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text for semantic matching."""
        # Common key phrases in FACT domain
        key_patterns = [
            r'\b\d+\s*hours?\b',           # Hours requirements
            r'\b\d+\s*years?\b',           # Years requirements  
            r'\$[\d,]+',                   # Dollar amounts
            r'\b\d+%\b',                   # Percentages
            r'\blicense\w*\b',             # License-related
            r'\bcontinuing\s+education\b', # CE requirements
            r'\brenewal\b',                # Renewal processes
            r'\bexam\w*\b',               # Exam-related
        ]
        
        phrases = []
        for pattern in key_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            phrases.extend(matches)
        
        return phrases
    
    def calculate_completeness_score(self, expected: str, retrieved: str) -> float:
        """Calculate how complete the retrieved answer is."""
        if not expected or not retrieved:
            return 0.0
        
        # Check if key information elements are present
        expected_elements = self._extract_information_elements(expected)
        retrieved_elements = self._extract_information_elements(retrieved)
        
        if not expected_elements:
            return 0.5  # Neutral if no clear structure
        
        matched_elements = sum(1 for elem in expected_elements 
                             if any(elem.lower() in ret.lower() 
                                   for ret in retrieved_elements))
        
        return matched_elements / len(expected_elements)
    
    def _extract_information_elements(self, text: str) -> List[str]:
        """Extract structured information elements from text."""
        elements = []
        
        # Numbers and quantities
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)
        elements.extend(numbers)
        
        # Dates and time periods
        dates = re.findall(r'\b\d{1,2}\/\d{1,2}\/\d{2,4}\b', text)
        elements.extend(dates)
        
        # Requirements and conditions
        requirements = re.findall(r'\brequire[sd]?\b.*?\.', text, re.IGNORECASE)
        elements.extend(requirements)
        
        # Named entities (states, organizations)
        named_entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        elements.extend(named_entities)
        
        return list(set(elements))  # Remove duplicates
    
    def calculate_clarity_score(self, text: str) -> float:
        """Calculate clarity/readability score of response."""
        if not text:
            return 0.0
        
        # Basic readability metrics
        sentences = re.split(r'[.!?]+', text)
        words = re.findall(r'\w+', text)
        
        if not sentences or not words:
            return 0.0
        
        # Average sentence length (target: 10-25 words)
        avg_sentence_length = len(words) / len(sentences)
        length_score = 1.0 - abs(avg_sentence_length - 17.5) / 17.5
        length_score = max(0.0, min(1.0, length_score))
        
        # Check for clear structure markers
        structure_markers = len(re.findall(r'\b(?:first|second|third|next|finally|however|therefore)\b', 
                                         text, re.IGNORECASE))
        structure_score = min(1.0, structure_markers * 0.2)
        
        # Penalize excessive jargon
        jargon_words = len(re.findall(r'\b(?:pursuant|heretofore|aforementioned|notwithstanding)\b', 
                                     text, re.IGNORECASE))
        jargon_penalty = min(0.3, jargon_words * 0.1)
        
        return max(0.0, (length_score + structure_score) * 0.5 - jargon_penalty)
    
    def calculate_authority_score(self, retrieved_answer: str, category: str, state: str) -> float:
        """Calculate authority/reliability score based on content markers."""
        if not retrieved_answer:
            return 0.0
        
        score = 0.5  # Base score
        text_lower = retrieved_answer.lower()
        
        # Authority indicators
        authority_markers = [
            'official', 'regulation', 'statute', 'code', 'department',
            'commission', 'board', 'license', 'certified', 'approved'
        ]
        
        marker_count = sum(1 for marker in authority_markers if marker in text_lower)
        authority_boost = min(0.3, marker_count * 0.05)
        
        # State-specific content bonus
        if state and state.lower() in text_lower:
            authority_boost += 0.1
        
        # Category-specific content bonus
        if category and any(cat_word in text_lower for cat_word in category.lower().split()):
            authority_boost += 0.1
        
        return min(1.0, score + authority_boost)
    
    def calculate_response_time_score(self, response_time_ms: float) -> float:
        """Convert response time to performance score."""
        if response_time_ms <= self.thresholds['excellent_response_time']:
            return 1.0
        elif response_time_ms <= self.thresholds['good_response_time']:
            return 0.8
        elif response_time_ms <= self.thresholds['poor_response_time']:
            return 0.4
        else:
            return 0.1
    
    def identify_failure_reasons(self, rubric: ScoringRubric, 
                               expected: str, retrieved: str) -> List[str]:
        """Identify specific reasons for poor performance."""
        reasons = []
        
        if rubric.exact_match < 0.1:
            reasons.append("No exact or near-exact match found")
        
        if rubric.semantic_similarity < 0.5:
            reasons.append("Low semantic similarity between expected and retrieved answers")
        
        if rubric.category_accuracy < 0.5:
            reasons.append("Incorrect category classification")
        
        if rubric.completeness < 0.5:
            reasons.append("Response lacks key information elements")
        
        if rubric.relevance < 0.5:
            reasons.append("Retrieved answer not relevant to query")
        
        if rubric.clarity < 0.3:
            reasons.append("Response clarity and readability issues")
        
        if rubric.response_time_score < 0.5:
            reasons.append("Poor response time performance")
        
        if rubric.confidence_score < 0.5:
            reasons.append("Low system confidence in response")
        
        if not retrieved:
            reasons.append("No answer retrieved from knowledge base")
        
        return reasons
    
    def generate_improvement_suggestions(self, rubric: ScoringRubric, 
                                       category: str, state: str) -> List[str]:
        """Generate specific improvement suggestions."""
        suggestions = []
        
        if rubric.semantic_similarity < 0.7:
            suggestions.append("Improve semantic search algorithms for better content matching")
        
        if rubric.category_accuracy < 0.8:
            suggestions.append(f"Review and improve category tagging for '{category}' topics")
        
        if rubric.state_relevance < 0.6 and state:
            suggestions.append(f"Add more {state}-specific content to knowledge base")
        
        if rubric.completeness < 0.7:
            suggestions.append("Expand answer completeness with additional details")
        
        if rubric.clarity < 0.6:
            suggestions.append("Improve answer formatting and structure for better readability")
        
        if rubric.response_time_score < 0.6:
            suggestions.append("Optimize retrieval algorithms and indexing for faster responses")
        
        if rubric.overall_score < 0.7:
            suggestions.append("Consider implementing hybrid search combining multiple retrieval methods")
        
        return suggestions
    
    def classify_performance_tier(self, overall_score: float) -> str:
        """Classify response into performance tier."""
        if overall_score >= 0.85:
            return "excellent"
        elif overall_score >= 0.70:
            return "good" 
        elif overall_score >= 0.50:
            return "needs_improvement"
        else:
            return "poor"
    
    async def analyze_response(self, test_data: Dict[str, Any]) -> AnalyzedResponse:
        """Analyze a single response using the comprehensive rubric."""
        
        # Extract test metadata
        test_id = test_data.get('test_id', f"test_{datetime.now().timestamp()}")
        persona = test_data.get('persona', 'unknown')
        category = test_data.get('category', '')
        state = test_data.get('state', '')
        difficulty = test_data.get('difficulty', 'medium')
        
        original_question = test_data.get('original_question', '')
        query_variation = test_data.get('query_variation', '')
        expected_answer = test_data.get('expected_answer', '')
        retrieved_answer = test_data.get('retrieved_answer', '')
        response_time_ms = test_data.get('response_time_ms', 0.0)
        match_type = test_data.get('match_type', 'none')
        system_confidence = test_data.get('confidence', 0.0)
        
        # Calculate scoring rubric
        rubric = ScoringRubric()
        
        # Accuracy scores
        rubric.exact_match = 1.0 if test_data.get('exact_match', False) else 0.0
        rubric.semantic_similarity = self.calculate_semantic_similarity(expected_answer, retrieved_answer)
        rubric.category_accuracy = 1.0 if test_data.get('category_match', False) else 0.0
        rubric.state_relevance = 1.0 if test_data.get('state_match', False) else 0.0
        
        # Quality scores
        rubric.completeness = self.calculate_completeness_score(expected_answer, retrieved_answer)
        rubric.relevance = max(rubric.semantic_similarity, rubric.exact_match)
        rubric.clarity = self.calculate_clarity_score(retrieved_answer)
        rubric.authority = self.calculate_authority_score(retrieved_answer, category, state)
        
        # Performance scores
        rubric.response_time_score = self.calculate_response_time_score(response_time_ms)
        rubric.confidence_score = system_confidence
        
        # Calculate overall score
        rubric.calculate_overall_score()
        
        # Identify issues and suggestions
        failure_reasons = self.identify_failure_reasons(rubric, expected_answer, retrieved_answer)
        improvement_suggestions = self.generate_improvement_suggestions(rubric, category, state)
        
        # Create analyzed response
        analyzed_response = AnalyzedResponse(
            test_id=test_id,
            timestamp=datetime.now(),
            persona=persona,
            category=category,
            state=state,
            difficulty=difficulty,
            original_question=original_question,
            query_variation=query_variation,
            expected_answer=expected_answer,
            retrieved_answer=retrieved_answer,
            response_time_ms=response_time_ms,
            match_type=match_type,
            system_confidence=system_confidence,
            scoring_rubric=rubric,
            failure_reasons=failure_reasons,
            improvement_suggestions=improvement_suggestions,
            performance_tier=self.classify_performance_tier(rubric.overall_score)
        )
        
        return analyzed_response
    
    async def analyze_batch(self, test_results: List[Dict[str, Any]]) -> List[AnalyzedResponse]:
        """Analyze a batch of test results."""
        logger.info(f"Analyzing batch of {len(test_results)} responses")
        
        analyzed_responses = []
        for i, test_data in enumerate(test_results):
            if i % 50 == 0 and i > 0:
                logger.info(f"Analyzed {i}/{len(test_results)} responses")
            
            analyzed_response = await self.analyze_response(test_data)
            analyzed_responses.append(analyzed_response)
        
        self.analyzed_responses.extend(analyzed_responses)
        logger.info(f"Completed analysis of {len(test_results)} responses")
        
        return analyzed_responses
    
    def save_analysis_results(self, filepath: str):
        """Save analysis results to JSON file."""
        results_data = {
            'metadata': {
                'analysis_timestamp': datetime.now().isoformat(),
                'total_responses': len(self.analyzed_responses),
                'analyzer_version': '1.0.0'
            },
            'analyzed_responses': [resp.to_dict() for resp in self.analyzed_responses]
        }
        
        with open(filepath, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        logger.info(f"Analysis results saved to {filepath}")
    
    def load_analysis_results(self, filepath: str) -> List[AnalyzedResponse]:
        """Load previously analyzed results."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        analyzed_responses = []
        for resp_data in data['analyzed_responses']:
            # Convert back to AnalyzedResponse objects
            rubric_data = resp_data['scoring_rubric']
            rubric = ScoringRubric(**rubric_data)
            
            resp_data['scoring_rubric'] = rubric
            resp_data['timestamp'] = datetime.fromisoformat(resp_data['timestamp'])
            
            analyzed_response = AnalyzedResponse(**resp_data)
            analyzed_responses.append(analyzed_response)
        
        self.analyzed_responses = analyzed_responses
        logger.info(f"Loaded {len(analyzed_responses)} analyzed responses from {filepath}")
        
        return analyzed_responses


async def main():
    """Test the performance analyzer."""
    # Sample test data
    sample_test_data = [
        {
            'test_id': 'test_001',
            'persona': 'insurance_agent',
            'category': 'licensing',
            'state': 'CA',
            'difficulty': 'medium',
            'original_question': 'What are the California insurance license requirements?',
            'query_variation': 'CA insurance license requirements',
            'expected_answer': 'California requires 20 hours of pre-licensing education and passing state exam.',
            'retrieved_answer': 'California insurance license requires 20 hours pre-licensing education and state exam.',
            'response_time_ms': 150.0,
            'match_type': 'fuzzy',
            'confidence': 0.9,
            'exact_match': False,
            'category_match': True,
            'state_match': True
        },
        {
            'test_id': 'test_002', 
            'persona': 'insurance_agent',
            'category': 'continuing_education',
            'state': 'TX',
            'difficulty': 'easy',
            'original_question': 'How many CE hours needed in Texas?',
            'query_variation': 'Texas CE hours requirement',
            'expected_answer': 'Texas requires 30 hours of continuing education every 2 years.',
            'retrieved_answer': '',
            'response_time_ms': 2500.0,
            'match_type': 'none',
            'confidence': 0.0,
            'exact_match': False,
            'category_match': False,
            'state_match': False
        }
    ]
    
    # Initialize analyzer
    analyzer = ResponseAnalysisEngine()
    await analyzer.initialize()
    
    # Analyze sample data
    analyzed_responses = await analyzer.analyze_batch(sample_test_data)
    
    # Print results
    for resp in analyzed_responses:
        print(f"\n=== Test {resp.test_id} ===")
        print(f"Persona: {resp.persona}")
        print(f"Category: {resp.category}")
        print(f"State: {resp.state}")
        print(f"Overall Score: {resp.scoring_rubric.overall_score:.3f} ({resp.scoring_rubric.grade_letter})")
        print(f"Performance Tier: {resp.performance_tier}")
        print(f"Failure Reasons: {resp.failure_reasons}")
        print(f"Suggestions: {resp.improvement_suggestions[:2]}")  # First 2 suggestions
    
    # Save results
    analyzer.save_analysis_results('tests/sample_analysis_results.json')
    
    # Cleanup
    await analyzer.db_manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
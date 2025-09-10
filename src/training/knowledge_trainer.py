"""
Knowledge Base Training System for FACT

This module provides training capabilities to improve the system's accuracy
based on user feedback and successful query patterns.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import structlog
from collections import defaultdict, Counter
import numpy as np

logger = structlog.get_logger(__name__)


@dataclass
class TrainingExample:
    """Represents a training example from user interaction."""
    query: str
    expected_answer: str
    actual_answer: Optional[str]
    feedback: str  # 'correct', 'incorrect', 'partial'
    score: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryPattern:
    """Learned query pattern from successful interactions."""
    pattern: str
    successful_matches: List[str]
    success_rate: float
    usage_count: int
    last_used: datetime


class KnowledgeTrainer:
    """
    Training system for improving knowledge base retrieval.
    
    Features:
    - Learn from user feedback
    - Adapt query patterns
    - Improve synonym mappings
    - Weight adjustments for scoring
    - Pattern recognition
    """
    
    def __init__(self, retriever=None, db_manager=None):
        """Initialize the knowledge trainer."""
        self.retriever = retriever
        self.db_manager = db_manager
        
        # Training data storage
        self.training_examples = []
        self.query_patterns = defaultdict(list)
        self.synonym_mappings = defaultdict(set)
        self.weight_adjustments = {
            'question_weight': 0.4,
            'answer_weight': 0.4,
            'keyword_weight': 0.4,
            'variation_weight': 0.2
        }
        
        # Performance tracking
        self.performance_history = []
        self.current_accuracy = 0.0
        self.target_accuracy = 0.967  # 96.7%
        
        # Learning parameters
        self.learning_rate = 0.1
        self.batch_size = 10
        self.min_confidence = 0.7
        
    async def train_from_feedback(self, query: str, result: Dict[str, Any], 
                                  feedback: str, user_expected: Optional[str] = None):
        """
        Train the system based on user feedback.
        
        Args:
            query: The user's query
            result: The system's response
            feedback: 'correct', 'incorrect', or 'partial'
            user_expected: Optional expected answer from user
        """
        # Create training example
        example = TrainingExample(
            query=query,
            expected_answer=user_expected or "",
            actual_answer=result.get('answer', ''),
            feedback=feedback,
            score=result.get('score', 0.0),
            timestamp=datetime.now(),
            metadata={
                'category': result.get('category'),
                'match_type': result.get('match_type'),
                'confidence': result.get('confidence', 0.0)
            }
        )
        
        self.training_examples.append(example)
        
        # Learn from the example
        await self._learn_from_example(example)
        
        # Update performance metrics
        await self._update_performance_metrics()
        
        logger.info(f"Training example recorded: {feedback} for query '{query[:50]}...'")
        
        # Trigger retraining if batch size reached
        if len(self.training_examples) % self.batch_size == 0:
            await self.retrain()
    
    async def _learn_from_example(self, example: TrainingExample):
        """Learn patterns from a single training example."""
        
        if example.feedback == 'correct':
            # Positive reinforcement
            await self._reinforce_positive(example)
        elif example.feedback == 'incorrect':
            # Negative reinforcement
            await self._reinforce_negative(example)
        else:  # partial
            # Partial reinforcement
            await self._reinforce_partial(example)
    
    async def _reinforce_positive(self, example: TrainingExample):
        """Reinforce patterns that led to correct answers."""
        # Extract successful patterns
        query_words = example.query.lower().split()
        
        # Store successful query pattern
        pattern_key = self._extract_pattern_key(example.query)
        self.query_patterns[pattern_key].append({
            'query': example.query,
            'answer': example.actual_answer,
            'score': example.score,
            'timestamp': example.timestamp
        })
        
        # Learn new synonyms from successful matches
        if example.metadata.get('match_type') == 'fuzzy':
            self._learn_synonyms(example.query, example.actual_answer)
        
        # Adjust weights based on success
        if example.score > 0.8:
            # Increase weight for the matching strategy that worked
            match_type = example.metadata.get('match_type', 'keyword')
            self._adjust_weights(match_type, increase=True)
    
    async def _reinforce_negative(self, example: TrainingExample):
        """Adjust patterns that led to incorrect answers."""
        # Identify what went wrong
        if example.score < 0.3:
            # Very low score - likely need new synonyms or patterns
            if example.expected_answer:
                self._learn_correction(example.query, example.expected_answer)
        
        # Decrease weight for the failing strategy
        match_type = example.metadata.get('match_type', 'keyword')
        self._adjust_weights(match_type, increase=False)
    
    async def _reinforce_partial(self, example: TrainingExample):
        """Handle partially correct answers."""
        # Small positive reinforcement
        if example.score > 0.5:
            match_type = example.metadata.get('match_type', 'keyword')
            self._adjust_weights(match_type, increase=True, factor=0.5)
    
    def _extract_pattern_key(self, query: str) -> str:
        """Extract a pattern key from a query."""
        # Simple pattern extraction - can be made more sophisticated
        words = query.lower().split()
        
        # Identify key patterns
        if 'requirements' in query.lower():
            return 'requirements_query'
        elif 'how' in query.lower():
            return 'how_to_query'
        elif 'what' in query.lower():
            return 'what_is_query'
        elif 'cost' in query.lower() or 'price' in query.lower():
            return 'cost_query'
        else:
            return 'general_query'
    
    def _learn_synonyms(self, query: str, answer: str):
        """Learn new synonym mappings from successful matches."""
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())
        
        # Find potential synonyms
        for q_word in query_words:
            for a_word in answer_words:
                if len(q_word) > 3 and len(a_word) > 3:
                    # Simple similarity check
                    if q_word[:3] == a_word[:3] or q_word[-3:] == a_word[-3:]:
                        self.synonym_mappings[q_word].add(a_word)
    
    def _learn_correction(self, query: str, expected_answer: str):
        """Learn from corrections provided by users."""
        # Extract keywords from both query and expected answer
        query_keywords = set(query.lower().split())
        answer_keywords = set(expected_answer.lower().split())
        
        # Find missing keywords that should be associated
        missing_keywords = answer_keywords - query_keywords
        
        for keyword in missing_keywords:
            if len(keyword) > 3:
                # Add to synonym mappings
                for q_word in query_keywords:
                    if len(q_word) > 3:
                        self.synonym_mappings[q_word].add(keyword)
    
    def _adjust_weights(self, match_type: str, increase: bool, factor: float = 1.0):
        """Adjust scoring weights based on success/failure."""
        adjustment = self.learning_rate * factor
        
        if not increase:
            adjustment = -adjustment
        
        if match_type == 'fuzzy':
            self.weight_adjustments['question_weight'] += adjustment
        elif match_type == 'keyword':
            self.weight_adjustments['keyword_weight'] += adjustment
        elif match_type == 'partial':
            self.weight_adjustments['variation_weight'] += adjustment
        
        # Normalize weights to sum to 1.0
        total = sum(self.weight_adjustments.values())
        for key in self.weight_adjustments:
            self.weight_adjustments[key] /= total
    
    async def retrain(self):
        """Retrain the retriever with learned patterns."""
        logger.info("Starting retraining with learned patterns...")
        
        if not self.retriever:
            logger.warning("No retriever configured for retraining")
            return
        
        # Apply learned synonyms to preprocessor
        if hasattr(self.retriever, 'preprocessor'):
            for word, synonyms in self.synonym_mappings.items():
                if word not in self.retriever.preprocessor.synonyms:
                    self.retriever.preprocessor.synonyms[word] = list(synonyms)
                else:
                    # Add new synonyms to existing ones
                    existing = set(self.retriever.preprocessor.synonyms[word])
                    existing.update(synonyms)
                    self.retriever.preprocessor.synonyms[word] = list(existing)
        
        # Apply weight adjustments if retriever supports it
        if hasattr(self.retriever, 'set_scoring_weights'):
            self.retriever.set_scoring_weights(self.weight_adjustments)
        
        # Refresh the retriever's index
        await self.retriever.refresh_index()
        
        logger.info(f"Retraining complete. New weights: {self.weight_adjustments}")
    
    async def _update_performance_metrics(self):
        """Update performance metrics based on recent examples."""
        if len(self.training_examples) < 10:
            return
        
        # Calculate accuracy from last 100 examples
        recent_examples = self.training_examples[-100:]
        correct = sum(1 for e in recent_examples if e.feedback == 'correct')
        partial = sum(0.5 for e in recent_examples if e.feedback == 'partial')
        total = len(recent_examples)
        
        self.current_accuracy = (correct + partial) / total if total > 0 else 0
        
        self.performance_history.append({
            'timestamp': datetime.now(),
            'accuracy': self.current_accuracy,
            'examples_count': len(self.training_examples)
        })
        
        logger.info(f"Current accuracy: {self.current_accuracy:.1%} (target: {self.target_accuracy:.1%})")
    
    async def suggest_improvements(self) -> List[Dict[str, Any]]:
        """Suggest improvements based on training data."""
        suggestions = []
        
        # Analyze failed queries
        failed_queries = [e for e in self.training_examples if e.feedback == 'incorrect']
        
        if failed_queries:
            # Group by pattern
            pattern_failures = defaultdict(list)
            for example in failed_queries:
                pattern = self._extract_pattern_key(example.query)
                pattern_failures[pattern].append(example)
            
            # Suggest improvements for each pattern
            for pattern, examples in pattern_failures.items():
                if len(examples) > 3:
                    suggestions.append({
                        'type': 'pattern_improvement',
                        'pattern': pattern,
                        'failure_count': len(examples),
                        'suggestion': f"Pattern '{pattern}' has {len(examples)} failures. Consider adding specific training data for this query type.",
                        'examples': [e.query for e in examples[:3]]
                    })
        
        # Suggest new synonyms
        if self.synonym_mappings:
            top_synonyms = sorted(
                self.synonym_mappings.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:5]
            
            for word, synonyms in top_synonyms:
                suggestions.append({
                    'type': 'synonym_suggestion',
                    'word': word,
                    'synonyms': list(synonyms),
                    'suggestion': f"Add synonyms for '{word}': {', '.join(list(synonyms)[:3])}"
                })
        
        # Suggest weight adjustments
        if self.current_accuracy < self.target_accuracy:
            suggestions.append({
                'type': 'weight_adjustment',
                'current_weights': self.weight_adjustments,
                'suggestion': "Consider manual weight tuning or more training examples"
            })
        
        return suggestions
    
    async def export_training_data(self, filepath: str):
        """Export training data for analysis or backup."""
        export_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'total_examples': len(self.training_examples),
                'current_accuracy': self.current_accuracy,
                'target_accuracy': self.target_accuracy
            },
            'training_examples': [
                {
                    'query': e.query,
                    'expected': e.expected_answer,
                    'actual': e.actual_answer,
                    'feedback': e.feedback,
                    'score': e.score,
                    'timestamp': e.timestamp.isoformat(),
                    'metadata': e.metadata
                }
                for e in self.training_examples
            ],
            'learned_patterns': dict(self.query_patterns),
            'synonym_mappings': {k: list(v) for k, v in self.synonym_mappings.items()},
            'weight_adjustments': self.weight_adjustments,
            'performance_history': self.performance_history
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Training data exported to {filepath}")
    
    async def import_training_data(self, filepath: str):
        """Import training data from a file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Import training examples
        for example_data in data.get('training_examples', []):
            example = TrainingExample(
                query=example_data['query'],
                expected_answer=example_data['expected'],
                actual_answer=example_data['actual'],
                feedback=example_data['feedback'],
                score=example_data['score'],
                timestamp=datetime.fromisoformat(example_data['timestamp']),
                metadata=example_data.get('metadata', {})
            )
            self.training_examples.append(example)
        
        # Import learned patterns
        self.query_patterns.update(data.get('learned_patterns', {}))
        
        # Import synonym mappings
        for word, synonyms in data.get('synonym_mappings', {}).items():
            self.synonym_mappings[word].update(synonyms)
        
        # Import weight adjustments
        self.weight_adjustments.update(data.get('weight_adjustments', {}))
        
        # Import performance history
        self.performance_history = data.get('performance_history', [])
        
        logger.info(f"Training data imported from {filepath}")
        
        # Apply learned patterns
        await self.retrain()
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Get current training statistics."""
        total_examples = len(self.training_examples)
        if total_examples == 0:
            return {
                'total_examples': 0,
                'accuracy': 0.0,
                'status': 'No training data'
            }
        
        correct = sum(1 for e in self.training_examples if e.feedback == 'correct')
        incorrect = sum(1 for e in self.training_examples if e.feedback == 'incorrect')
        partial = sum(1 for e in self.training_examples if e.feedback == 'partial')
        
        return {
            'total_examples': total_examples,
            'correct': correct,
            'incorrect': incorrect,
            'partial': partial,
            'accuracy': self.current_accuracy,
            'target_accuracy': self.target_accuracy,
            'learned_synonyms': len(self.synonym_mappings),
            'learned_patterns': len(self.query_patterns),
            'current_weights': self.weight_adjustments,
            'improvement_needed': self.target_accuracy - self.current_accuracy,
            'status': 'Training' if self.current_accuracy < self.target_accuracy else 'Optimized'
        }


# Convenience functions for web API integration
async def train_from_api_feedback(query: str, result: Dict, feedback: str):
    """Train from API feedback - for integration with web endpoints."""
    from retrieval.enhanced_search import EnhancedRetriever
    
    retriever = EnhancedRetriever()
    trainer = KnowledgeTrainer(retriever)
    
    await trainer.train_from_feedback(query, result, feedback)
    
    return trainer.get_training_stats()


async def get_training_suggestions():
    """Get improvement suggestions based on training data."""
    trainer = KnowledgeTrainer()
    
    # Load existing training data if available
    try:
        await trainer.import_training_data('data/training_history.json')
    except FileNotFoundError:
        pass
    
    return await trainer.suggest_improvements()
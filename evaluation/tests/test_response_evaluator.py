"""
Tests for FACT System Response Evaluator
"""

import unittest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

from ..core.response_evaluator import (
    ResponseEvaluator, EvaluationResult, EvaluationCriteria
)
from ..config.scoring_rubric import PersonaType, ScoreDimension

class TestResponseEvaluator(unittest.TestCase):
    """Test cases for response evaluator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.evaluator = ResponseEvaluator(enable_ai_scoring=False)
        self.sample_criteria = EvaluationCriteria(
            question="What are your pricing plans?",
            expected_elements=["pricing", "features", "value"],
            persona=PersonaType.PRICE_CONSCIOUS,
            context={"test": True}
        )
    
    def test_evaluator_initialization(self):
        """Test evaluator initialization."""
        evaluator = ResponseEvaluator()
        self.assertIsNotNone(evaluator.scoring_rubric)
        self.assertFalse(evaluator.enable_ai_scoring)
        
        # Test with AI enabled
        ai_evaluator = ResponseEvaluator(enable_ai_scoring=True)
        self.assertTrue(ai_evaluator.enable_ai_scoring)
    
    async def test_basic_evaluation(self):
        """Test basic response evaluation."""
        response_text = """
        Our pricing starts at $29/month for the basic plan with essential features.
        The professional plan is $79/month and includes advanced analytics and priority support.
        Both plans offer great value with 24/7 customer support and a 30-day money-back guarantee.
        """
        
        result = await self.evaluator.evaluate_response(
            response_id="test_001",
            response_text=response_text,
            evaluation_criteria=self.sample_criteria
        )
        
        # Check result structure
        self.assertIsInstance(result, EvaluationResult)
        self.assertEqual(result.response_id, "test_001")
        self.assertEqual(result.persona, PersonaType.PRICE_CONSCIOUS)
        self.assertIsInstance(result.weighted_score, float)
        self.assertGreaterEqual(result.weighted_score, 0.0)
        self.assertLessEqual(result.weighted_score, 100.0)
        
        # Check that all dimensions were scored
        expected_dimensions = {dim.value for dim in ScoreDimension}
        actual_dimensions = set(result.dimension_scores.keys())
        self.assertEqual(expected_dimensions, actual_dimensions)
    
    def test_accuracy_scoring(self):
        """Test accuracy dimension scoring."""
        response_with_claims = "Our product has 99.9% uptime and costs $50/month."
        score, factors = self.evaluator._score_accuracy(
            response_with_claims, self.sample_criteria
        )
        
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)
        self.assertIsInstance(factors, list)
    
    def test_completeness_scoring(self):
        """Test completeness dimension scoring."""
        # Response covering all expected elements
        complete_response = "Our pricing includes competitive rates, comprehensive features, and excellent value for your investment."
        
        score, factors = self.evaluator._score_completeness(
            complete_response, self.sample_criteria
        )
        
        # Should score higher due to covering expected elements
        self.assertGreater(score, 50.0)
        
        # Incomplete response
        incomplete_response = "We have different plans available."
        
        score_incomplete, factors_incomplete = self.evaluator._score_completeness(
            incomplete_response, self.sample_criteria
        )
        
        # Should score lower
        self.assertLess(score_incomplete, score)
    
    def test_relevance_scoring(self):
        """Test relevance dimension scoring."""
        # Highly relevant response
        relevant_response = "Our pricing plans are designed to offer flexible options for different business needs."
        
        score, factors = self.evaluator._score_relevance(
            relevant_response, self.sample_criteria
        )
        
        self.assertGreater(score, 60.0)  # Should score reasonably well
        
        # Less relevant response
        irrelevant_response = "Our company was founded in 1995 and we have great customer service."
        
        score_irrelevant, factors_irrelevant = self.evaluator._score_relevance(
            irrelevant_response, self.sample_criteria
        )
        
        self.assertLess(score_irrelevant, score)
    
    def test_clarity_scoring(self):
        """Test clarity dimension scoring."""
        # Clear, well-structured response
        clear_response = """
        We offer three pricing tiers:
        1. Basic: $29/month
        2. Professional: $79/month
        3. Enterprise: Custom pricing
        
        Each plan includes different features to meet your needs.
        """
        
        score, factors = self.evaluator._score_clarity(
            clear_response, self.sample_criteria
        )
        
        # Should score well due to structure
        self.assertGreater(score, 70.0)
        
        # Unclear response
        unclear_response = "We have pricing and it's good and there are different options that you can choose from depending on what you need and want."
        
        score_unclear, factors_unclear = self.evaluator._score_clarity(
            unclear_response, self.sample_criteria
        )
        
        self.assertLess(score_unclear, score)
    
    def test_persona_fit_scoring(self):
        """Test persona fit dimension scoring."""
        # Price-conscious focused response
        price_focused = "Our affordable plans start at just $29/month, offering excellent value with cost-effective solutions and budget-friendly options."
        
        score, factors = self.evaluator._score_persona_fit(
            price_focused, self.sample_criteria
        )
        
        # Should score well for price-conscious persona
        self.assertGreater(score, 60.0)
        
        # Non-price focused response  
        feature_focused = "Our advanced enterprise solutions provide cutting-edge technology and premium features."
        
        score_feature, factors_feature = self.evaluator._score_persona_fit(
            feature_focused, self.sample_criteria
        )
        
        self.assertLess(score_feature, score)
    
    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        dimension_scores = {
            "accuracy": 80.0,
            "completeness": 75.0,
            "relevance": 85.0,
            "clarity": 70.0,
            "persona_fit": 78.0
        }
        
        evaluation_details = {
            "accuracy": {"method": "rule_based"},
            "completeness": {"method": "rule_based"},
            "relevance": {"method": "rule_based"},
            "clarity": {"method": "rule_based"},
            "persona_fit": {"method": "rule_based"}
        }
        
        confidence = self.evaluator._calculate_confidence_score(
            dimension_scores, evaluation_details
        )
        
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    def test_text_similarity_calculation(self):
        """Test text similarity calculation."""
        text1 = "The quick brown fox jumps over the lazy dog"
        text2 = "A quick brown fox jumps over a lazy dog"
        
        similarity = self.evaluator._calculate_text_similarity(text1, text2)
        
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
        self.assertGreater(similarity, 0.5)  # Should be quite similar
    
    def test_factual_claims_extraction(self):
        """Test factual claims extraction."""
        text_with_facts = "Our service has 99.9% uptime. We have 1000+ customers. The basic plan costs $29/month."
        
        claims = self.evaluator._extract_factual_claims(text_with_facts)
        
        self.assertIsInstance(claims, list)
        self.assertGreater(len(claims), 0)
    
    def test_key_terms_extraction(self):
        """Test key terms extraction."""
        text = "Our pricing plans include basic and professional options with different features"
        
        terms = self.evaluator._extract_key_terms(text)
        
        self.assertIsInstance(terms, list)
        self.assertIn("pricing", terms)
        self.assertIn("plans", terms)
        self.assertNotIn("the", terms)  # Stop words should be filtered
    
    async def test_batch_evaluation(self):
        """Test batch evaluation of multiple responses."""
        responses = [
            {
                "id": "batch_001",
                "response": "Our basic plan is $29/month with great value.",
                "criteria": {
                    "question": "What are your prices?",
                    "expected_elements": ["pricing"],
                    "persona": PersonaType.PRICE_CONSCIOUS,
                    "context": {}
                }
            },
            {
                "id": "batch_002", 
                "response": "Let me break this down simply: Step 1: Choose a plan. Step 2: Sign up. Step 3: Get started.",
                "criteria": {
                    "question": "How do I get started?",
                    "expected_elements": ["steps", "guidance"],
                    "persona": PersonaType.OVERWHELMED,
                    "context": {}
                }
            }
        ]
        
        results = await self.evaluator.batch_evaluate(responses)
        
        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], EvaluationResult)
        self.assertIsInstance(results[1], EvaluationResult)

class AsyncTestCase(unittest.IsolatedAsyncioTestCase):
    """Async test case for response evaluator."""
    
    async def test_async_evaluation(self):
        """Test asynchronous evaluation."""
        evaluator = ResponseEvaluator(enable_ai_scoring=False)
        criteria = EvaluationCriteria(
            question="Test question",
            expected_elements=["test"],
            persona=PersonaType.PRICE_CONSCIOUS,
            context={}
        )
        
        result = await evaluator.evaluate_response(
            response_id="async_test",
            response_text="This is a test response about pricing and value.",
            evaluation_criteria=criteria
        )
        
        self.assertIsInstance(result, EvaluationResult)
        self.assertEqual(result.response_id, "async_test")

if __name__ == "__main__":
    unittest.main()
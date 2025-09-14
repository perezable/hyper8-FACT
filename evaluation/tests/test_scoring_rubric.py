"""
Tests for FACT System Scoring Rubric Configuration
"""

import unittest
from ..config.scoring_rubric import (
    SCORING_RUBRIC, ScoreDimension, PersonaType, ScoringRubric
)

class TestScoringRubric(unittest.TestCase):
    """Test cases for scoring rubric configuration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.rubric = SCORING_RUBRIC
    
    def test_dimension_weights_sum_to_one(self):
        """Test that all dimension weights sum to 1.0."""
        total_weight = sum(
            dim.weight for dim in self.rubric.dimensions.values()
        )
        self.assertAlmostEqual(total_weight, 1.0, places=3)
    
    def test_all_dimensions_present(self):
        """Test that all required dimensions are present."""
        expected_dimensions = {
            ScoreDimension.ACCURACY,
            ScoreDimension.COMPLETENESS,
            ScoreDimension.RELEVANCE,
            ScoreDimension.CLARITY,
            ScoreDimension.PERSONA_FIT
        }
        actual_dimensions = set(self.rubric.dimensions.keys())
        self.assertEqual(expected_dimensions, actual_dimensions)
    
    def test_dimension_weights_are_valid(self):
        """Test that all dimension weights are valid percentages."""
        for dimension, config in self.rubric.dimensions.items():
            self.assertGreaterEqual(config.weight, 0.0)
            self.assertLessEqual(config.weight, 1.0)
    
    def test_accuracy_has_highest_weight(self):
        """Test that accuracy has the highest weight (40%)."""
        accuracy_weight = self.rubric.dimensions[ScoreDimension.ACCURACY].weight
        self.assertEqual(accuracy_weight, 0.40)
        
        # Verify it's the highest
        for dimension, config in self.rubric.dimensions.items():
            if dimension != ScoreDimension.ACCURACY:
                self.assertLessEqual(config.weight, accuracy_weight)
    
    def test_all_personas_have_criteria(self):
        """Test that all persona types have scoring criteria."""
        expected_personas = {
            PersonaType.PRICE_CONSCIOUS,
            PersonaType.OVERWHELMED,
            PersonaType.SKEPTICAL,
            PersonaType.TIME_PRESSED,
            PersonaType.AMBITIOUS
        }
        actual_personas = set(self.rubric.persona_criteria.keys())
        self.assertEqual(expected_personas, actual_personas)
    
    def test_persona_criteria_completeness(self):
        """Test that each persona has complete criteria."""
        for persona, criteria in self.rubric.persona_criteria.items():
            # Check required attributes
            self.assertIsInstance(criteria.emphasis_keywords, list)
            self.assertIsInstance(criteria.required_elements, list)
            self.assertIsInstance(criteria.bonus_criteria, list)
            self.assertIsInstance(criteria.penalty_criteria, list)
            
            # Check that lists are not empty
            self.assertGreater(len(criteria.emphasis_keywords), 0)
            self.assertGreater(len(criteria.required_elements), 0)
    
    def test_price_conscious_keywords(self):
        """Test that price-conscious persona has appropriate keywords."""
        price_conscious = self.rubric.persona_criteria[PersonaType.PRICE_CONSCIOUS]
        expected_keywords = {"cost", "price", "budget", "value", "affordable"}
        actual_keywords = set(price_conscious.emphasis_keywords)
        
        # Check that expected keywords are present
        self.assertTrue(expected_keywords.issubset(actual_keywords))
    
    def test_weighted_score_calculation(self):
        """Test weighted score calculation."""
        # Test data with known weights
        dimension_scores = {
            ScoreDimension.ACCURACY: 80.0,      # 40% weight
            ScoreDimension.COMPLETENESS: 70.0,  # 20% weight  
            ScoreDimension.RELEVANCE: 75.0,     # 20% weight
            ScoreDimension.CLARITY: 85.0,       # 10% weight
            ScoreDimension.PERSONA_FIT: 90.0    # 10% weight
        }
        
        expected_score = (80 * 0.4) + (70 * 0.2) + (75 * 0.2) + (85 * 0.1) + (90 * 0.1)
        # = 32 + 14 + 15 + 8.5 + 9 = 78.5
        
        actual_score = self.rubric.calculate_weighted_score(dimension_scores)
        self.assertAlmostEqual(actual_score, 78.5, places=1)
    
    def test_score_categorization(self):
        """Test score category determination."""
        test_cases = [
            (95.0, "excellent"),
            (85.0, "good"),  
            (75.0, "good"),
            (65.0, "adequate"),
            (45.0, "poor"),
            (15.0, "failed")
        ]
        
        for score, expected_category in test_cases:
            category, description = self.rubric.get_score_category(score)
            self.assertEqual(category, expected_category)
            self.assertIsInstance(description, str)
    
    def test_dimension_weight_retrieval(self):
        """Test dimension weight retrieval method."""
        accuracy_weight = self.rubric.get_dimension_weight(ScoreDimension.ACCURACY)
        self.assertEqual(accuracy_weight, 0.40)
        
        clarity_weight = self.rubric.get_dimension_weight(ScoreDimension.CLARITY)
        self.assertEqual(clarity_weight, 0.10)
    
    def test_persona_criteria_retrieval(self):
        """Test persona criteria retrieval method."""
        skeptical_criteria = self.rubric.get_persona_criteria(PersonaType.SKEPTICAL)
        
        self.assertEqual(skeptical_criteria.persona, PersonaType.SKEPTICAL)
        self.assertIn("proof", skeptical_criteria.emphasis_keywords)
        self.assertIn("evidence", skeptical_criteria.emphasis_keywords)
    
    def test_rubric_validation(self):
        """Test rubric weight validation."""
        self.assertTrue(self.rubric.validate_scoring_weights())
    
    def test_dimension_criteria_structure(self):
        """Test that each dimension has proper criteria structure."""
        for dimension, config in self.rubric.dimensions.items():
            # Check required attributes
            self.assertIsInstance(config.name, str)
            self.assertIsInstance(config.weight, float)
            self.assertIsInstance(config.description, str)
            self.assertIsInstance(config.criteria, dict)
            
            # Check criteria keys
            expected_keys = {"90-100", "70-89", "50-69", "30-49", "0-29"}
            actual_keys = set(config.criteria.keys())
            self.assertEqual(expected_keys, actual_keys)

class TestScoringRubricInitialization(unittest.TestCase):
    """Test scoring rubric initialization and setup."""
    
    def test_fresh_rubric_creation(self):
        """Test creating a new rubric instance."""
        new_rubric = ScoringRubric()
        
        # Should have same structure as global instance
        self.assertEqual(len(new_rubric.dimensions), 5)
        self.assertEqual(len(new_rubric.persona_criteria), 5)
        self.assertTrue(new_rubric.validate_scoring_weights())
    
    def test_rubric_consistency(self):
        """Test that multiple rubric instances are consistent."""
        rubric1 = ScoringRubric()
        rubric2 = ScoringRubric()
        
        # Should have same weights
        for dimension in ScoreDimension:
            weight1 = rubric1.get_dimension_weight(dimension)
            weight2 = rubric2.get_dimension_weight(dimension)
            self.assertEqual(weight1, weight2)

if __name__ == "__main__":
    unittest.main()
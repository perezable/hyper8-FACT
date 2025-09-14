"""
FACT System Response Evaluator
AI-powered evaluation of response quality using comprehensive scoring rubric.
"""

import json
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import asyncio
import logging

from ..config.scoring_rubric import (
    SCORING_RUBRIC, ScoreDimension, PersonaType, PersonaScoring
)

@dataclass
class EvaluationResult:
    """Result of response evaluation with detailed scoring."""
    response_id: str
    question: str
    response: str
    persona: PersonaType
    dimension_scores: Dict[str, float]
    weighted_score: float
    score_category: str
    score_description: str
    evaluation_details: Dict[str, Any]
    confidence_score: float
    timestamp: datetime
    evaluator_version: str = "1.0.0"

@dataclass
class EvaluationCriteria:
    """Criteria for evaluating a specific response."""
    question: str
    expected_elements: List[str]
    persona: PersonaType
    context: Dict[str, Any]
    reference_answer: Optional[str] = None

class ResponseEvaluator:
    """AI-powered response evaluator using comprehensive scoring rubric."""
    
    def __init__(self, ai_client=None, enable_ai_scoring: bool = True):
        """
        Initialize the response evaluator.
        
        Args:
            ai_client: AI client for qualitative assessment (Claude/GPT-4)
            enable_ai_scoring: Whether to use AI for scoring (fallback to rule-based)
        """
        self.scoring_rubric = SCORING_RUBRIC
        self.ai_client = ai_client
        self.enable_ai_scoring = enable_ai_scoring
        self.logger = logging.getLogger(__name__)
        
    async def evaluate_response(
        self,
        response_id: str,
        response_text: str,
        evaluation_criteria: EvaluationCriteria
    ) -> EvaluationResult:
        """
        Evaluate a response against the scoring rubric.
        
        Args:
            response_id: Unique identifier for the response
            response_text: The response text to evaluate
            evaluation_criteria: Criteria for evaluation
            
        Returns:
            EvaluationResult with detailed scoring
        """
        self.logger.info(f"Starting evaluation for response {response_id}")
        
        # Score each dimension
        dimension_scores = {}
        evaluation_details = {}
        
        for dimension in ScoreDimension:
            score, details = await self._score_dimension(
                dimension, response_text, evaluation_criteria
            )
            dimension_scores[dimension.value] = score
            evaluation_details[dimension.value] = details
            
        # Calculate weighted total score
        dimension_score_enum = {
            ScoreDimension(k): v for k, v in dimension_scores.items()
        }
        weighted_score = self.scoring_rubric.calculate_weighted_score(dimension_score_enum)
        
        # Get score category
        score_category, score_description = self.scoring_rubric.get_score_category(weighted_score)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            dimension_scores, evaluation_details
        )
        
        return EvaluationResult(
            response_id=response_id,
            question=evaluation_criteria.question,
            response=response_text,
            persona=evaluation_criteria.persona,
            dimension_scores=dimension_scores,
            weighted_score=weighted_score,
            score_category=score_category,
            score_description=score_description,
            evaluation_details=evaluation_details,
            confidence_score=confidence_score,
            timestamp=datetime.now()
        )
    
    async def _score_dimension(
        self,
        dimension: ScoreDimension,
        response_text: str,
        criteria: EvaluationCriteria
    ) -> Tuple[float, Dict[str, Any]]:
        """Score a specific dimension of the response."""
        
        if self.enable_ai_scoring and self.ai_client:
            return await self._ai_score_dimension(dimension, response_text, criteria)
        else:
            return self._rule_based_score_dimension(dimension, response_text, criteria)
    
    async def _ai_score_dimension(
        self,
        dimension: ScoreDimension,
        response_text: str,
        criteria: EvaluationCriteria
    ) -> Tuple[float, Dict[str, Any]]:
        """Use AI to score a dimension (Claude/GPT-4)."""
        
        dimension_config = self.scoring_rubric.dimensions[dimension]
        persona_config = self.scoring_rubric.get_persona_criteria(criteria.persona)
        
        scoring_prompt = self._build_scoring_prompt(
            dimension, dimension_config, persona_config, response_text, criteria
        )
        
        try:
            # Make AI API call (implementation depends on your AI client)
            ai_response = await self._call_ai_evaluator(scoring_prompt)
            
            # Parse AI response
            score, reasoning = self._parse_ai_response(ai_response)
            
            details = {
                "method": "ai_powered",
                "reasoning": reasoning,
                "ai_confidence": self._extract_ai_confidence(ai_response)
            }
            
            return score, details
            
        except Exception as e:
            self.logger.warning(f"AI scoring failed for {dimension.value}: {e}")
            # Fallback to rule-based scoring
            return self._rule_based_score_dimension(dimension, response_text, criteria)
    
    def _rule_based_score_dimension(
        self,
        dimension: ScoreDimension,
        response_text: str,
        criteria: EvaluationCriteria
    ) -> Tuple[float, Dict[str, Any]]:
        """Rule-based scoring for a dimension."""
        
        score = 50.0  # Base score
        details = {"method": "rule_based", "factors": []}
        
        if dimension == ScoreDimension.ACCURACY:
            score, factors = self._score_accuracy(response_text, criteria)
        elif dimension == ScoreDimension.COMPLETENESS:
            score, factors = self._score_completeness(response_text, criteria)
        elif dimension == ScoreDimension.RELEVANCE:
            score, factors = self._score_relevance(response_text, criteria)
        elif dimension == ScoreDimension.CLARITY:
            score, factors = self._score_clarity(response_text, criteria)
        elif dimension == ScoreDimension.PERSONA_FIT:
            score, factors = self._score_persona_fit(response_text, criteria)
        
        details["factors"] = factors
        return score, details
    
    def _score_accuracy(self, response: str, criteria: EvaluationCriteria) -> Tuple[float, List[str]]:
        """Rule-based accuracy scoring."""
        score = 70.0  # Base accuracy score
        factors = []
        
        # Check for common accuracy indicators
        if criteria.reference_answer:
            # Compare against reference answer (simplified)
            similarity = self._calculate_text_similarity(response, criteria.reference_answer)
            if similarity > 0.8:
                score += 20
                factors.append("High similarity to reference answer")
            elif similarity > 0.6:
                score += 10
                factors.append("Moderate similarity to reference answer")
        
        # Check for factual claims that might need verification
        factual_claims = self._extract_factual_claims(response)
        if factual_claims:
            factors.append(f"Contains {len(factual_claims)} factual claims requiring verification")
        
        # Check for hedging language (indicates uncertainty)
        hedging_words = ["might", "possibly", "perhaps", "likely", "probably"]
        hedging_count = sum(1 for word in hedging_words if word in response.lower())
        if hedging_count > 3:
            score -= 10
            factors.append("Excessive hedging language suggests uncertainty")
        
        return min(100.0, max(0.0, score)), factors
    
    def _score_completeness(self, response: str, criteria: EvaluationCriteria) -> Tuple[float, List[str]]:
        """Rule-based completeness scoring."""
        score = 60.0  # Base completeness score
        factors = []
        
        # Check if expected elements are covered
        covered_elements = 0
        for element in criteria.expected_elements:
            if element.lower() in response.lower():
                covered_elements += 1
                factors.append(f"Covers expected element: {element}")
        
        if criteria.expected_elements:
            coverage_ratio = covered_elements / len(criteria.expected_elements)
            score += coverage_ratio * 40  # Up to 40 points for complete coverage
        
        # Check response length (longer responses tend to be more complete)
        word_count = len(response.split())
        if word_count > 200:
            score += 10
            factors.append("Comprehensive length suggests thoroughness")
        elif word_count < 50:
            score -= 15
            factors.append("Short response may lack completeness")
        
        return min(100.0, max(0.0, score)), factors
    
    def _score_relevance(self, response: str, criteria: EvaluationCriteria) -> Tuple[float, List[str]]:
        """Rule-based relevance scoring."""
        score = 70.0  # Base relevance score
        factors = []
        
        # Extract key terms from question
        question_terms = self._extract_key_terms(criteria.question)
        response_terms = self._extract_key_terms(response)
        
        # Calculate term overlap
        overlap = len(set(question_terms) & set(response_terms))
        if question_terms:
            overlap_ratio = overlap / len(question_terms)
            score += overlap_ratio * 25
            factors.append(f"Term overlap ratio: {overlap_ratio:.2f}")
        
        # Check for direct question addressing
        if "?" in criteria.question:
            question_words = ["what", "how", "why", "when", "where", "who"]
            for word in question_words:
                if word in criteria.question.lower() and word in response.lower():
                    score += 5
                    factors.append(f"Addresses question word: {word}")
        
        return min(100.0, max(0.0, score)), factors
    
    def _score_clarity(self, response: str, criteria: EvaluationCriteria) -> Tuple[float, List[str]]:
        """Rule-based clarity scoring."""
        score = 70.0  # Base clarity score
        factors = []
        
        # Check sentence length (shorter sentences are clearer)
        sentences = re.split(r'[.!?]+', response)
        avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / max(1, len([s for s in sentences if s.strip()]))
        
        if avg_sentence_length < 15:
            score += 10
            factors.append("Good sentence length for readability")
        elif avg_sentence_length > 25:
            score -= 10
            factors.append("Long sentences may reduce clarity")
        
        # Check for structure indicators
        structure_words = ["first", "second", "next", "finally", "however", "therefore"]
        structure_count = sum(1 for word in structure_words if word in response.lower())
        if structure_count > 0:
            score += 5
            factors.append("Uses structural language for clarity")
        
        # Check for bullet points or numbered lists
        if re.search(r'[•\-\*]\s|^\d+\.\s', response, re.MULTILINE):
            score += 10
            factors.append("Uses lists for better organization")
        
        return min(100.0, max(0.0, score)), factors
    
    def _score_persona_fit(self, response: str, criteria: EvaluationCriteria) -> Tuple[float, List[str]]:
        """Rule-based persona fit scoring."""
        score = 50.0  # Base persona fit score
        factors = []
        
        persona_config = self.scoring_rubric.get_persona_criteria(criteria.persona)
        
        # Check for emphasis keywords
        keyword_matches = sum(1 for keyword in persona_config.emphasis_keywords 
                             if keyword in response.lower())
        if keyword_matches > 0:
            score += min(25, keyword_matches * 5)
            factors.append(f"Contains {keyword_matches} persona-relevant keywords")
        
        # Check required elements
        element_matches = sum(1 for element in persona_config.required_elements
                             if any(term in response.lower() for term in element.lower().split()))
        if element_matches > 0:
            score += min(20, element_matches * 10)
            factors.append(f"Meets {element_matches} persona requirements")
        
        # Check for bonus criteria
        bonus_matches = sum(1 for bonus in persona_config.bonus_criteria
                           if any(term in response.lower() for term in bonus.lower().split()))
        if bonus_matches > 0:
            score += min(15, bonus_matches * 8)
            factors.append(f"Includes {bonus_matches} bonus elements")
        
        # Check for penalty criteria
        penalty_matches = sum(1 for penalty in persona_config.penalty_criteria
                             if any(term in response.lower() for term in penalty.lower().split()))
        if penalty_matches > 0:
            score -= min(20, penalty_matches * 10)
            factors.append(f"Contains {penalty_matches} penalty elements")
        
        return min(100.0, max(0.0, score)), factors
    
    def _calculate_confidence_score(
        self, 
        dimension_scores: Dict[str, float],
        evaluation_details: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for the evaluation."""
        
        # Base confidence
        confidence = 0.7
        
        # Increase confidence if AI was used
        ai_powered_dimensions = sum(1 for details in evaluation_details.values() 
                                   if details.get("method") == "ai_powered")
        confidence += (ai_powered_dimensions / len(dimension_scores)) * 0.2
        
        # Decrease confidence for extreme scores (might indicate poor evaluation)
        extreme_scores = sum(1 for score in dimension_scores.values() 
                           if score < 20 or score > 95)
        confidence -= (extreme_scores / len(dimension_scores)) * 0.1
        
        # Increase confidence if scores are consistent across dimensions
        scores = list(dimension_scores.values())
        if scores:
            score_variance = sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores)
            if score_variance < 100:  # Low variance
                confidence += 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def _build_scoring_prompt(
        self,
        dimension: ScoreDimension,
        dimension_config,
        persona_config: PersonaScoring,
        response_text: str,
        criteria: EvaluationCriteria
    ) -> str:
        """Build prompt for AI-powered scoring."""
        
        return f"""
        You are an expert evaluator for customer service responses. 
        
        EVALUATION TASK:
        Score the following response on the dimension of {dimension_config.name} (0-100 scale).
        
        DIMENSION DESCRIPTION:
        {dimension_config.description}
        
        SCORING CRITERIA:
        {json.dumps(dimension_config.criteria, indent=2)}
        
        CUSTOMER PERSONA: {criteria.persona.value}
        Persona Requirements:
        - Emphasis keywords: {persona_config.emphasis_keywords}
        - Required elements: {persona_config.required_elements}
        - Bonus criteria: {persona_config.bonus_criteria}
        - Penalty criteria: {persona_config.penalty_criteria}
        
        QUESTION ASKED:
        {criteria.question}
        
        RESPONSE TO EVALUATE:
        {response_text}
        
        INSTRUCTIONS:
        1. Analyze the response against the scoring criteria
        2. Consider the persona requirements
        3. Provide a score from 0-100
        4. Explain your reasoning
        5. Rate your confidence in the evaluation (0-100)
        
        RESPONSE FORMAT:
        {{
            "score": <numeric score 0-100>,
            "reasoning": "<detailed explanation>",
            "confidence": <confidence score 0-100>
        }}
        """
    
    async def _call_ai_evaluator(self, prompt: str) -> str:
        """Call AI API for evaluation (placeholder - implement based on your AI client)."""
        # This is a placeholder - implement based on your AI client (Claude/OpenAI)
        if not self.ai_client:
            raise Exception("No AI client configured")
        
        # Example for different AI clients:
        # return await self.ai_client.complete(prompt)
        
        # Placeholder response for testing
        return json.dumps({
            "score": 75,
            "reasoning": "Response provides good information but could be more specific to the persona",
            "confidence": 80
        })
    
    def _parse_ai_response(self, ai_response: str) -> Tuple[float, str]:
        """Parse AI response to extract score and reasoning."""
        try:
            response_data = json.loads(ai_response)
            score = float(response_data.get("score", 50))
            reasoning = response_data.get("reasoning", "No reasoning provided")
            return score, reasoning
        except (json.JSONDecodeError, ValueError):
            # Fallback parsing
            score_match = re.search(r'"score":\s*(\d+)', ai_response)
            score = float(score_match.group(1)) if score_match else 50.0
            
            reasoning_match = re.search(r'"reasoning":\s*"([^"]+)"', ai_response)
            reasoning = reasoning_match.group(1) if reasoning_match else "Unable to parse reasoning"
            
            return score, reasoning
    
    def _extract_ai_confidence(self, ai_response: str) -> float:
        """Extract confidence score from AI response."""
        try:
            response_data = json.loads(ai_response)
            return float(response_data.get("confidence", 70)) / 100.0
        except (json.JSONDecodeError, ValueError):
            confidence_match = re.search(r'"confidence":\s*(\d+)', ai_response)
            confidence = float(confidence_match.group(1)) if confidence_match else 70.0
            return confidence / 100.0
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity (placeholder for more sophisticated methods)."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union) if union else 0.0
    
    def _extract_factual_claims(self, text: str) -> List[str]:
        """Extract potential factual claims from text."""
        # Simple implementation - could be enhanced with NLP
        claims = []
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            if any(word in sentence.lower() for word in ["is", "are", "has", "have", "costs", "includes"]):
                claims.append(sentence.strip())
        return claims
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text."""
        # Simple keyword extraction - could be enhanced with NLP
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return [word for word in words if word not in stop_words]
    
    async def batch_evaluate(
        self,
        responses: List[Dict[str, Any]]
    ) -> List[EvaluationResult]:
        """Evaluate multiple responses in batch."""
        tasks = []
        for response_data in responses:
            criteria = EvaluationCriteria(**response_data['criteria'])
            task = self.evaluate_response(
                response_data['id'],
                response_data['response'],
                criteria
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
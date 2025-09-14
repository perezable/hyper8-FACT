"""
FACT System Response Scoring Rubric Configuration
Comprehensive evaluation framework for response quality assessment.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum

class ScoreDimension(Enum):
    """Core scoring dimensions for response evaluation."""
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    RELEVANCE = "relevance"
    CLARITY = "clarity"
    PERSONA_FIT = "persona_fit"

class ScoreRange(Enum):
    """Score ranges with descriptive labels."""
    EXCELLENT = (90, 100, "Perfect answer with extras")
    GOOD = (70, 89, "Solid answer, minor gaps")
    ADEQUATE = (50, 69, "Basic answer, some issues")
    POOR = (30, 49, "Significant problems")
    FAILED = (0, 29, "Wrong or missing answer")

class PersonaType(Enum):
    """Customer persona types for tailored evaluation."""
    PRICE_CONSCIOUS = "price_conscious"
    OVERWHELMED = "overwhelmed"
    SKEPTICAL = "skeptical"
    TIME_PRESSED = "time_pressed"
    AMBITIOUS = "ambitious"

@dataclass
class ScoringDimension:
    """Configuration for a single scoring dimension."""
    name: str
    weight: float
    description: str
    criteria: Dict[str, str]
    max_score: int = 100

@dataclass
class PersonaScoring:
    """Persona-specific scoring criteria."""
    persona: PersonaType
    emphasis_keywords: List[str]
    required_elements: List[str]
    bonus_criteria: List[str]
    penalty_criteria: List[str]

class ScoringRubric:
    """Comprehensive scoring rubric for FACT system responses."""
    
    def __init__(self):
        self.dimensions = self._initialize_dimensions()
        self.persona_criteria = self._initialize_persona_criteria()
        self.score_ranges = self._initialize_score_ranges()
        
    def _initialize_dimensions(self) -> Dict[ScoreDimension, ScoringDimension]:
        """Initialize scoring dimensions with weights and criteria."""
        return {
            ScoreDimension.ACCURACY: ScoringDimension(
                name="Accuracy",
                weight=0.40,
                description="Factual correctness and reliability of information",
                criteria={
                    "90-100": "All facts verified and correct, no misleading information",
                    "70-89": "Mostly accurate with minor factual errors",
                    "50-69": "Generally accurate but contains some incorrect details",
                    "30-49": "Multiple factual errors that could mislead",
                    "0-29": "Predominantly incorrect or unverified information"
                }
            ),
            ScoreDimension.COMPLETENESS: ScoringDimension(
                name="Completeness",
                weight=0.20,
                description="Covers all relevant aspects of the question",
                criteria={
                    "90-100": "Comprehensive coverage of all question aspects plus helpful extras",
                    "70-89": "Addresses main points with minor omissions",
                    "50-69": "Covers basic requirements but misses important details",
                    "30-49": "Incomplete response missing key information",
                    "0-29": "Severely incomplete or off-topic response"
                }
            ),
            ScoreDimension.RELEVANCE: ScoringDimension(
                name="Relevance",
                weight=0.20,
                description="Directly addresses the specific question asked",
                criteria={
                    "90-100": "Perfectly targeted to question with no tangential content",
                    "70-89": "Mostly relevant with minimal off-topic content",
                    "50-69": "Generally relevant but includes some unrelated information",
                    "30-49": "Partially relevant with significant off-topic content",
                    "0-29": "Largely irrelevant or misunderstands the question"
                }
            ),
            ScoreDimension.CLARITY: ScoringDimension(
                name="Clarity",
                weight=0.10,
                description="Easy to understand and well-structured",
                criteria={
                    "90-100": "Crystal clear, excellent structure, perfect readability",
                    "70-89": "Clear and well-organized with minor clarity issues",
                    "50-69": "Generally understandable but could be clearer",
                    "30-49": "Somewhat confusing structure or language",
                    "0-29": "Difficult to understand, poor structure"
                }
            ),
            ScoreDimension.PERSONA_FIT: ScoringDimension(
                name="Persona Fit",
                weight=0.10,
                description="Appropriate tone and content for customer type",
                criteria={
                    "90-100": "Perfect match for persona with optimal tone and focus",
                    "70-89": "Good persona alignment with minor mismatches",
                    "50-69": "Adequate persona consideration but could be better tailored",
                    "30-49": "Poor persona fit, inappropriate tone or focus",
                    "0-29": "No consideration of persona or completely inappropriate"
                }
            )
        }
    
    def _initialize_persona_criteria(self) -> Dict[PersonaType, PersonaScoring]:
        """Initialize persona-specific scoring criteria."""
        return {
            PersonaType.PRICE_CONSCIOUS: PersonaScoring(
                persona=PersonaType.PRICE_CONSCIOUS,
                emphasis_keywords=[
                    "cost", "price", "budget", "affordable", "value", "savings",
                    "ROI", "cost-effective", "economical", "discount"
                ],
                required_elements=[
                    "Pricing information clearly stated",
                    "Value proposition explained",
                    "Cost comparisons when relevant"
                ],
                bonus_criteria=[
                    "Mentions savings opportunities",
                    "Provides cost breakdowns",
                    "Explains long-term value"
                ],
                penalty_criteria=[
                    "Ignores price concerns",
                    "Pushes expensive options without justification",
                    "Lacks cost transparency"
                ]
            ),
            PersonaType.OVERWHELMED: PersonaScoring(
                persona=PersonaType.OVERWHELMED,
                emphasis_keywords=[
                    "simple", "easy", "step-by-step", "guide", "help", "support",
                    "straightforward", "clear", "basic", "beginner"
                ],
                required_elements=[
                    "Simple, jargon-free language",
                    "Clear step-by-step instructions",
                    "Reassuring tone"
                ],
                bonus_criteria=[
                    "Breaks complex topics into digestible parts",
                    "Offers ongoing support options",
                    "Provides encouragement"
                ],
                penalty_criteria=[
                    "Uses technical jargon without explanation",
                    "Provides overwhelming amount of information",
                    "Condescending tone"
                ]
            ),
            PersonaType.SKEPTICAL: PersonaScoring(
                persona=PersonaType.SKEPTICAL,
                emphasis_keywords=[
                    "proof", "evidence", "data", "statistics", "research",
                    "verified", "tested", "proven", "guarantee", "results"
                ],
                required_elements=[
                    "Provides concrete evidence",
                    "Cites credible sources",
                    "Addresses common concerns"
                ],
                bonus_criteria=[
                    "Includes third-party validation",
                    "Provides case studies or testimonials",
                    "Offers trial periods or guarantees"
                ],
                penalty_criteria=[
                    "Makes unsupported claims",
                    "Lacks credible evidence",
                    "Dismisses legitimate concerns"
                ]
            ),
            PersonaType.TIME_PRESSED: PersonaScoring(
                persona=PersonaType.TIME_PRESSED,
                emphasis_keywords=[
                    "quick", "fast", "immediate", "now", "urgent", "efficient",
                    "streamlined", "automated", "instant", "rapid"
                ],
                required_elements=[
                    "Concise, to-the-point responses",
                    "Prioritizes most important information",
                    "Clear action items"
                ],
                bonus_criteria=[
                    "Provides shortcuts or quick wins",
                    "Emphasizes time-saving benefits",
                    "Offers immediate next steps"
                ],
                penalty_criteria=[
                    "Overly verbose responses",
                    "Buries key information",
                    "Lacks clear priorities"
                ]
            ),
            PersonaType.AMBITIOUS: PersonaScoring(
                persona=PersonaType.AMBITIOUS,
                emphasis_keywords=[
                    "growth", "scale", "expansion", "advanced", "competitive",
                    "opportunity", "potential", "strategic", "optimize", "maximize"
                ],
                required_elements=[
                    "Focus on growth opportunities",
                    "Strategic perspective",
                    "Scalability considerations"
                ],
                bonus_criteria=[
                    "Discusses competitive advantages",
                    "Provides growth roadmap",
                    "Emphasizes potential returns"
                ],
                penalty_criteria=[
                    "Focuses only on basic features",
                    "Lacks strategic vision",
                    "Doesn't address scalability"
                ]
            )
        }
    
    def _initialize_score_ranges(self) -> Dict[str, tuple]:
        """Initialize score ranges with descriptions."""
        return {
            "excellent": (90, 100, "Perfect answer with extras"),
            "good": (70, 89, "Solid answer, minor gaps"),
            "adequate": (50, 69, "Basic answer, some issues"),
            "poor": (30, 49, "Significant problems"),
            "failed": (0, 29, "Wrong or missing answer")
        }
    
    def get_dimension_weight(self, dimension: ScoreDimension) -> float:
        """Get the weight for a specific scoring dimension."""
        return self.dimensions[dimension].weight
    
    def get_persona_criteria(self, persona: PersonaType) -> PersonaScoring:
        """Get scoring criteria for a specific persona."""
        return self.persona_criteria[persona]
    
    def calculate_weighted_score(self, dimension_scores: Dict[ScoreDimension, float]) -> float:
        """Calculate weighted total score from dimension scores."""
        total_score = 0.0
        for dimension, score in dimension_scores.items():
            weight = self.get_dimension_weight(dimension)
            total_score += score * weight
        return round(total_score, 2)
    
    def get_score_category(self, score: float) -> tuple:
        """Get score category and description based on numeric score."""
        for category, (min_score, max_score, description) in self.score_ranges.items():
            if min_score <= score <= max_score:
                return category, description
        return "unknown", "Score out of range"
    
    def validate_scoring_weights(self) -> bool:
        """Validate that all dimension weights sum to 1.0."""
        total_weight = sum(dim.weight for dim in self.dimensions.values())
        return abs(total_weight - 1.0) < 0.001  # Allow for floating point precision

# Global rubric instance
SCORING_RUBRIC = ScoringRubric()
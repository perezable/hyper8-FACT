"""
FACT System Response Evaluation Framework
Comprehensive scoring and quality assessment for customer service responses.
"""

from .config.scoring_rubric import (
    SCORING_RUBRIC,
    ScoreDimension,
    PersonaType,
    ScoreRange,
    ScoringDimension,
    PersonaScoring,
    ScoringRubric
)

from .core.response_evaluator import (
    ResponseEvaluator,
    EvaluationResult,
    EvaluationCriteria
)

from .metrics.quality_metrics import (
    QualityMetricsCalculator,
    QualityMetrics,
    TrendAnalysis,
    QUALITY_METRICS_CALCULATOR
)

__version__ = "1.0.0"

__all__ = [
    # Configuration
    "SCORING_RUBRIC",
    "ScoreDimension",
    "PersonaType", 
    "ScoreRange",
    "ScoringDimension",
    "PersonaScoring",
    "ScoringRubric",
    
    # Core evaluation
    "ResponseEvaluator",
    "EvaluationResult",
    "EvaluationCriteria",
    
    # Quality metrics
    "QualityMetricsCalculator",
    "QualityMetrics",
    "TrendAnalysis",
    "QUALITY_METRICS_CALCULATOR"
]
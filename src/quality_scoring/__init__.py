"""
FACT Knowledge Base Quality Scoring System

This package provides comprehensive quality assessment and scoring
for knowledge base entries, optimizing for deployment readiness
and persona coverage.
"""

from .quality_specialist import QualitySpecialist, QualityMetrics, PersonaCoverage, KnowledgeEntry

__version__ = "1.0.0"
__all__ = ["QualitySpecialist", "QualityMetrics", "PersonaCoverage", "KnowledgeEntry"]
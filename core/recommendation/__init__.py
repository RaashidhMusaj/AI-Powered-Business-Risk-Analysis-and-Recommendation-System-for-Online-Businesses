"""
Core Recommendation Module Package.
Provides automated business risk recommendations based on BusinessRiskResult.
"""

from .engine.recommendation_engine import RecommendationEngine
from .dto.recommendation_context import RecommendationContext
from .dto.recommendation_result import RecommendationResult, RecommendationReport
from .exceptions.recommendation_exception import RecommendationError, RecommendationGenerationError

__all__ = [
    "RecommendationEngine",
    "RecommendationContext",
    "RecommendationResult",
    "RecommendationReport",
    "RecommendationError",
    "RecommendationGenerationError",
]

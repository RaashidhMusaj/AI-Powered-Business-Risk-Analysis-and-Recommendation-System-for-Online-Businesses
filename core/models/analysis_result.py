"""
Unified System Analysis Result DTO.
Combines BusinessRiskResult and RecommendationResult into a single system-level outcome.
"""

from dataclasses import dataclass
from core.business_risk.models.business_risk_result import BusinessRiskResult
from core.recommendation.dto.recommendation_result import RecommendationResult


@dataclass(frozen=True)
class AnalysisResult:
    """
    System-level container combining Business Risk Analysis results and Recommendation Engine results.
    """

    business_risk: BusinessRiskResult
    recommendation: RecommendationResult

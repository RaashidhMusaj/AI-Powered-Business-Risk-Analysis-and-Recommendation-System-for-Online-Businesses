"""
Recommendation Service Component.
Provides a thin facade isolating external callers from internal RecommendationEngine details.
"""

import logging
from typing import Optional

from core.business_risk.models.business_risk_result import BusinessRiskResult
from core.recommendation.dto.recommendation_result import RecommendationResult
from core.recommendation.engine.recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Thin integration service delegating calls to RecommendationEngine.
    """

    def __init__(self, engine: Optional[RecommendationEngine] = None):
        """
        Initializes RecommendationService with an optional RecommendationEngine instance.
        """
        logger.info("Initializing RecommendationService facade")
        self.engine = engine or RecommendationEngine()

    def generate_recommendation(self, risk_result: BusinessRiskResult) -> RecommendationResult:
        """
        Delegates recommendation generation to the underlying engine.

        :param risk_result: Input BusinessRiskResult.
        :return: Immutable RecommendationResult.
        """
        logger.info("RecommendationService.generate_recommendation called")
        return self.engine.generate_recommendation(risk_result)

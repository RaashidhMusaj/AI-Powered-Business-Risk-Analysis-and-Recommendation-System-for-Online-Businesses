"""
Recommendation Engine Core Component.
Orchestrates sub-components to transform BusinessRiskResult into a RecommendationResult.
Stateless and thread-safe for multi-tenant execution.
"""

import logging
import time
from typing import Optional

from core.business_risk.models.business_risk_result import BusinessRiskResult
from core.recommendation.dto.recommendation_result import RecommendationResult
from core.recommendation.interpreter.risk_interpreter import RiskInterpreter
from core.recommendation.selector import ActionSelector
from core.recommendation.report import ReportBuilder
from core.recommendation.formatter import ResponseFormatter
from core.recommendation.exceptions import (
    RecommendationError,
    RecommendationGenerationError,
)

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Central orchestrator for the Recommendation Module.
    Coordinates sub-components via dependency injection.
    Stateless and thread-safe for concurrent tenant executions.
    """

    def __init__(
        self,
        interpreter: Optional[RiskInterpreter] = None,
        selector: Optional[ActionSelector] = None,
        report_builder: Optional[ReportBuilder] = None,
        formatter: Optional[ResponseFormatter] = None,
        builder: Optional[ReportBuilder] = None,
    ):
        """
        Initializes RecommendationEngine with constructor dependency injection.

        :param interpreter: Optional RiskInterpreter instance.
        :param selector: Optional ActionSelector instance.
        :param report_builder: Optional ReportBuilder instance.
        :param formatter: Optional ResponseFormatter instance.
        :param builder: Optional ReportBuilder instance (legacy alias for report_builder).
        """
        logger.info("Initializing RecommendationEngine with sub-component dependencies")
        self.interpreter = interpreter or RiskInterpreter()
        self.selector = selector or ActionSelector()
        self.report_builder = report_builder or builder or ReportBuilder()
        self.formatter = formatter or ResponseFormatter()

    def generate_recommendation(self, risk_result: BusinessRiskResult) -> RecommendationResult:
        """
        Generates a RecommendationResult from an input BusinessRiskResult.
        Single public entrypoint for the end-to-end recommendation pipeline.

        :param risk_result: Input BusinessRiskResult from Business Risk module.
        :return: Immutable RecommendationResult object.
        :raises RecommendationGenerationError: If input is invalid or execution fails unexpectedly.
        :raises RecommendationError: Re-raises domain recommendation exceptions without wrapping.
        """
        logger.info(f"Generating business risk recommendation for result: {risk_result}")

        if risk_result is None or not isinstance(risk_result, BusinessRiskResult):
            logger.error("Invalid input: risk_result must be a valid BusinessRiskResult instance.")
            raise RecommendationGenerationError("Expected valid BusinessRiskResult instance.")

        try:
            start_time = time.perf_counter()

            # Pipeline execution:
            # 1. RiskInterpreter -> RecommendationContext
            context = self.interpreter.interpret(risk_result)

            # 2. ActionSelector -> SelectionResult
            selection_result = self.selector.select(context)

            # 3. ReportBuilder -> RecommendationReport
            report = self.report_builder.build(selection_result)

            # 4. ResponseFormatter -> RecommendationResult
            recommendation_result = self.formatter.format(report, start_time)

            return recommendation_result

        except RecommendationError as exc:
            logger.error(f"RecommendationError caught during recommendation generation: {exc}")
            raise
        except Exception as ex:
            logger.error(f"Unexpected error in recommendation pipeline: {ex}", exc_info=True)
            raise RecommendationGenerationError(f"Recommendation generation failed: {ex}") from ex

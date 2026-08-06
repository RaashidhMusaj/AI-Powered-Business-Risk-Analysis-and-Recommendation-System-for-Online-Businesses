"""
Response Formatter Main Component.
Orchestrates validation, timing, mapping, and response packaging for RecommendationReport objects.
"""

import logging
import time
from typing import Optional, Any

from core.recommendation.dto.recommendation_result import RecommendationResult
from core.recommendation.formatter.validator import ResponseValidator
from core.recommendation.formatter.mapper import ResponseMapper

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """
    Presentation boundary of Recommendation Engine.
    Converts RecommendationReport objects into public RecommendationResult DTOs.
    """

    def __init__(
        self,
        validator: Optional[ResponseValidator] = None,
        mapper: Optional[ResponseMapper] = None,
    ):
        """
        Initializes ResponseFormatter with constructor injection for validator and mapper.

        :param validator: Optional ResponseValidator instance.
        :param mapper: Optional ResponseMapper instance.
        """
        self.validator = validator or ResponseValidator()
        self.mapper = mapper or ResponseMapper()
        logger.info("Initialized ResponseFormatter with validator and mapper components")

    def format(
        self,
        report: Any,
        start_time: float,
    ) -> RecommendationResult:
        """
        Validates report, calculates execution timing, maps metadata, and constructs RecommendationResult.

        :param report: RecommendationReport from Phase 6.
        :param start_time: Execution start timestamp measured with time.perf_counter().
        :return: Immutable RecommendationResult object.
        """
        logger.info("Formatting RecommendationReport into RecommendationResult")
        self.validator.validate(report)

        now = time.perf_counter()
        elapsed_ms = int(round((now - start_time) * 1000.0))
        processing_time_ms = max(0, elapsed_ms)

        return self.mapper.to_result(report, processing_time_ms=processing_time_ms)

    def format_response(
        self,
        report: Any,
        start_time: float = 0.0,
        context: Optional[Any] = None,
    ) -> RecommendationResult:
        """
        Backwards-compatible alias for format().

        :param report: RecommendationReport instance.
        :param start_time: Execution start timestamp measured with time.perf_counter().
        :param context: Optional RecommendationContext.
        :return: RecommendationResult instance.
        """
        return self.format(report, start_time)

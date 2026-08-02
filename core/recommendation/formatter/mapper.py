"""
Response Mapper Component.
Maps RecommendationReport objects to RecommendationResult DTOs.
"""

import logging
from typing import Any

from core.recommendation.constants.versions import RECOMMENDATION_VERSION
from core.recommendation.dto.recommendation_result import RecommendationResult, RecommendationMetadata

logger = logging.getLogger(__name__)


class ResponseMapper:
    """
    Maps RecommendationReport payload and execution parameters into a RecommendationResult instance.
    """

    def to_result(
        self,
        report: Any,
        processing_time_ms: int = 0,
        version: str = RECOMMENDATION_VERSION,
    ) -> RecommendationResult:
        """
        Converts RecommendationReport into a strongly-typed RecommendationResult with structured metadata.

        :param report: RecommendationReport from Phase 6.
        :param processing_time_ms: Elapsed execution time in integer milliseconds.
        :param version: API result format version.
        :return: Immutable RecommendationResult instance.
        """
        logger.info("Mapping RecommendationReport to RecommendationResult")
        iso_generated_at = report.generated_at.isoformat()

        highest_priority = getattr(report, "highest_priority", "")
        recommendation_count = getattr(report, "recommendation_count", 0)

        metadata = RecommendationMetadata(
            highest_priority=highest_priority,
            recommendation_count=recommendation_count,
            generated_at=iso_generated_at,
        )

        return RecommendationResult(
            report=report,
            metadata=metadata,
            generated_timestamp=report.generated_at,
            version=version,
            processing_time_ms=processing_time_ms,
        )

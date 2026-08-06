"""
Response Validator Component.
Validates RecommendationReport payloads before formatting.
"""

import logging
from datetime import datetime
from typing import Any

from core.recommendation.formatter.exceptions import ResponseValidationError

logger = logging.getLogger(__name__)


class ResponseValidator:
    """
    Validates RecommendationReport structures to ensure all required fields and content are present.
    """

    def validate(self, report: Any) -> None:
        """
        Validates that report is not None and contains valid generated_at, summary, insights, and actions.

        Validation sequence:
        1. report is not None
        2. generated_at is present and is a datetime
        3. summary exists and is non-empty
        4. insights exists and is non-empty
        5. actions exists and is non-empty

        :param report: RecommendationReport to validate.
        :raises ResponseValidationError: If any validation check fails.
        """
        if report is None:
            logger.error("Validation failed: RecommendationReport cannot be None.")
            raise ResponseValidationError("RecommendationReport cannot be None.")

        if not hasattr(report, "generated_at") or report.generated_at is None or not isinstance(report.generated_at, datetime):
            logger.error("Validation failed: RecommendationReport generated_at is missing or invalid.")
            raise ResponseValidationError("RecommendationReport generated_at must be a valid datetime.")

        if not hasattr(report, "summary") or report.summary is None or not str(report.summary).strip():
            logger.error("Validation failed: RecommendationReport summary is empty or missing.")
            raise ResponseValidationError("RecommendationReport summary cannot be empty.")

        if not hasattr(report, "insights") or report.insights is None or len(report.insights) == 0:
            logger.error("Validation failed: RecommendationReport insights are empty or missing.")
            raise ResponseValidationError("RecommendationReport insights cannot be empty.")

        if not hasattr(report, "actions") or report.actions is None or len(report.actions) == 0:
            logger.error("Validation failed: RecommendationReport actions are empty or missing.")
            raise ResponseValidationError("RecommendationReport actions cannot be empty.")

        logger.info("RecommendationReport validation passed successfully.")

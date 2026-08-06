"""
Report Builder Specific Exceptions.
"""

import logging
from core.recommendation.exceptions.recommendation_exception import RecommendationError

logger = logging.getLogger(__name__)


class ReportError(RecommendationError):
    """
    Base exception for all Report Builder errors.
    """
    pass


class ReportValidationError(ReportError):
    """
    Exception raised when SelectionResult validation fails (null or empty selection).
    """
    pass


class ReportBuildError(ReportError):
    """
    Exception raised when template resolution, rendering, or report assembly fails.
    """
    pass

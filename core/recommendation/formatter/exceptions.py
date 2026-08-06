"""
Response Formatter Specific Exceptions.
"""

import logging
from core.recommendation.exceptions.recommendation_exception import RecommendationError

logger = logging.getLogger(__name__)


class ResponseFormattingError(RecommendationError):
    """
    Base exception for Response Formatter component errors.
    """

    pass


class ResponseValidationError(ResponseFormattingError):
    """
    Exception raised when RecommendationReport validation fails.
    """

    pass

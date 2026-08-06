"""
Recommendation Module Custom Exceptions.
Provides domain-specific exceptions for recommendation generation failures.
"""

import logging

logger = logging.getLogger(__name__)


class RecommendationError(Exception):
    """
    Base domain exception for all Recommendation Module errors.
    """

    def __init__(self, message: str = "An error occurred in the Recommendation Module"):
        self.message = message
        logger.error(f"RecommendationError raised: {self.message}")
        super().__init__(self.message)


class RecommendationGenerationError(RecommendationError):
    """
    Exception raised when recommendation engine fails during evaluation or report generation.
    """

    def __init__(self, message: str = "Failed to generate business risk recommendation"):
        super().__init__(message)

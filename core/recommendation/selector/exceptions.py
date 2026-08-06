"""
Action Selector Specific Exceptions.
"""

import logging
from core.recommendation.exceptions.recommendation_exception import RecommendationError

logger = logging.getLogger(__name__)


class SelectionError(RecommendationError):
    """
    Base exception for all Action Selector errors.
    """
    pass


class SelectionValidationError(SelectionError):
    """
    Exception raised when selection input context is invalid.
    """
    pass


class SelectionFailedError(SelectionError):
    """
    Exception raised when no matching recommendation rules could be selected.
    """
    pass

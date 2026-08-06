"""
Template Manager Specific Exceptions.
"""

import logging
from core.recommendation.exceptions.recommendation_exception import RecommendationError

logger = logging.getLogger(__name__)


class TemplateError(RecommendationError):
    """
    Base exception for all Template Manager errors.
    """
    pass


class TemplateValidationError(TemplateError):
    """
    Exception raised when template validation fails (duplicate IDs, bad category, invalid placeholders).
    """
    pass


class TemplateNotFoundError(TemplateError):
    """
    Exception raised when template directory is missing or template ID is not found.
    """
    pass


class TemplateRenderingError(TemplateError):
    """
    Exception raised when template string formatting fails or placeholder values are missing.
    """
    pass

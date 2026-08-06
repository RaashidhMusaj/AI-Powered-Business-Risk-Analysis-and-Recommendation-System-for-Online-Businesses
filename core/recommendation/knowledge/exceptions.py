"""
Knowledge Base Specific Exceptions.
"""

import logging
from core.recommendation.exceptions.recommendation_exception import RecommendationError

logger = logging.getLogger(__name__)


class KnowledgeBaseError(RecommendationError):
    """
    Base exception for all Knowledge Base errors.
    """
    pass


class KnowledgeValidationError(KnowledgeBaseError):
    """
    Exception raised when rule validation fails (duplicate IDs, invalid schema, bad aspect/risk).
    """
    pass


class KnowledgeNotFoundError(KnowledgeBaseError):
    """
    Exception raised when knowledge data directory or files are missing/empty.
    """
    pass

"""
Recommendation Knowledge Base Package.
Provides read-only rule storage, validation, indexing, and lookup facade.
"""

from .models import RecommendationRule
from .exceptions import KnowledgeBaseError, KnowledgeValidationError, KnowledgeNotFoundError
from .loader import KnowledgeLoader
from .validator import KnowledgeValidator
from .repository import KnowledgeRepository
from .knowledge_base import RecommendationKnowledgeBase

__all__ = [
    "RecommendationRule",
    "KnowledgeBaseError",
    "KnowledgeValidationError",
    "KnowledgeNotFoundError",
    "KnowledgeLoader",
    "KnowledgeValidator",
    "KnowledgeRepository",
    "RecommendationKnowledgeBase",
]

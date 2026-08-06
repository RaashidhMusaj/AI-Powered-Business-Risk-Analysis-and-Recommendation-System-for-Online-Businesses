"""
Templates package for Recommendation Module.
Provides template loading, validation, repository indexing, rendering, and facade.
"""

from .models import RecommendationTemplate
from .exceptions import TemplateError, TemplateValidationError, TemplateNotFoundError, TemplateRenderingError
from .loader import TemplateLoader
from .validator import TemplateValidator
from .repository import TemplateRepository
from .renderer import TemplateRenderer
from .manager import TemplateManager

__all__ = [
    "RecommendationTemplate",
    "TemplateError",
    "TemplateValidationError",
    "TemplateNotFoundError",
    "TemplateRenderingError",
    "TemplateLoader",
    "TemplateValidator",
    "TemplateRepository",
    "TemplateRenderer",
    "TemplateManager",
]

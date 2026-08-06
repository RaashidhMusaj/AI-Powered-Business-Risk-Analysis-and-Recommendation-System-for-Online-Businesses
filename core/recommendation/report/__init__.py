"""
Report Builder Package.
Transforms SelectionResult into structured RecommendationReport objects.
"""

from .models import RecommendationReport
from .exceptions import ReportError, ReportValidationError, ReportBuildError
from .resolver import TemplateResolver
from .validator import ReportValidator
from .assembler import ReportAssembler
from .builder import ReportBuilder

__all__ = [
    "RecommendationReport",
    "ReportError",
    "ReportValidationError",
    "ReportBuildError",
    "TemplateResolver",
    "ReportValidator",
    "ReportAssembler",
    "ReportBuilder",
]

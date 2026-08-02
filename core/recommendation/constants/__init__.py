"""
Constants package for Recommendation Module.
"""

from .aspects import VALID_ASPECTS
from .priorities import VALID_PRIORITIES
from .risk_levels import VALID_RISK_LEVELS
from .template_categories import VALID_TEMPLATE_CATEGORIES
from .business_statuses import VALID_BUSINESS_STATUSES
from .versions import RECOMMENDATION_VERSION

__all__ = [
    "VALID_ASPECTS",
    "VALID_PRIORITIES",
    "VALID_RISK_LEVELS",
    "VALID_TEMPLATE_CATEGORIES",
    "VALID_BUSINESS_STATUSES",
    "RECOMMENDATION_VERSION",
]


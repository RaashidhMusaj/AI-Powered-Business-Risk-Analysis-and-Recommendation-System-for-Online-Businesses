"""
Template Model for Recommendation Module.
Defines immutable RecommendationTemplate schema.
"""

import logging
from dataclasses import dataclass, field
from typing import Tuple

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RecommendationTemplate:
    """
    Immutable representation of a recommendation text formatting template.
    """

    id: str
    category: str  # SUMMARY, INSIGHT, ACTION
    template: str
    placeholders: Tuple[str, ...] = field(default_factory=tuple)
    enabled: bool = True

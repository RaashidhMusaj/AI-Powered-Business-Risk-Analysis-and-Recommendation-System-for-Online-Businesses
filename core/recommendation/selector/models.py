"""
Action Selector Data Models.
Defines immutable output representations for selected recommendation rules.
"""

import logging
from dataclasses import dataclass
from typing import Tuple

from core.recommendation.knowledge.models import RecommendationRule

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SelectedRecommendation:
    """
    Immutable representation of an individually selected recommendation rule.
    """

    aspect: str
    risk_level: str
    rule: RecommendationRule
    priority: str


@dataclass(frozen=True)
class SelectionResult:
    """
    Immutable collection container holding all selected recommendations and metadata.
    """

    selected: Tuple[SelectedRecommendation, ...]
    highest_priority: str
    recommendation_count: int

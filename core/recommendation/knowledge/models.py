"""
Knowledge Base Rule Model.
Defines immutable RecommendationRule schema.
"""

import logging
from dataclasses import dataclass, field
from typing import Tuple

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RecommendationRule:
    """
    Immutable representation of a single business recommendation rule.
    """

    id: str
    aspect: str
    risk_level: str
    title: str
    description: str
    actions: Tuple[str, ...]
    priority: str = "HIGH"
    tags: Tuple[str, ...] = field(default_factory=tuple)
    version: int = 1
    enabled: bool = True

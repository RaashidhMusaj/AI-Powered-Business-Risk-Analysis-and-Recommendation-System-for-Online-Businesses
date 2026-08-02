"""
Report Builder Data Models.
Defines immutable output representations for completed business recommendation reports.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RecommendationReport:
    """
    Immutable representation of a completed business recommendation report.
    """

    summary: str
    insights: Tuple[str, ...]
    actions: Tuple[str, ...]
    highest_priority: str
    recommendation_count: int
    generated_at: datetime

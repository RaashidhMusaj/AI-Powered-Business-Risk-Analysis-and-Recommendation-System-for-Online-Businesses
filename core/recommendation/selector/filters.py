"""
Selection Filters Component.
Provides filtering utilities for candidate SelectedRecommendation items.
"""

import logging
from typing import List, Set

from core.recommendation.selector.models import SelectedRecommendation

logger = logging.getLogger(__name__)


class DeduplicationFilter:
    """
    Deduplicates candidate SelectedRecommendation objects by underlying rule.id.
    """

    @staticmethod
    def filter(candidates: List[SelectedRecommendation]) -> List[SelectedRecommendation]:
        """
        Filters out duplicate recommendation rules by rule ID.
        
        :param candidates: List of candidate SelectedRecommendation items.
        :return: List of unique SelectedRecommendation items.
        """
        seen_ids: Set[str] = set()
        deduped: List[SelectedRecommendation] = []

        for item in candidates:
            rule_id = item.rule.id
            if rule_id not in seen_ids:
                seen_ids.add(rule_id)
                deduped.append(item)

        logger.info(f"DeduplicationFilter: reduced {len(candidates)} candidates to {len(deduped)} unique rules.")
        return deduped

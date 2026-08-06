"""
Selection Strategy Component.
Encapsulates recommendation rule selection policy, merging, deduplication, and priority sorting.
"""

import logging
from typing import List, Dict, Any, Optional

from core.recommendation.dto.recommendation_context import RecommendationContext
from core.recommendation.knowledge.knowledge_base import RecommendationKnowledgeBase
from core.recommendation.knowledge.models import RecommendationRule
from core.recommendation.selector.models import SelectedRecommendation, SelectionResult
from core.recommendation.selector.filters import DeduplicationFilter
from core.recommendation.selector.exceptions import SelectionValidationError, SelectionFailedError

logger = logging.getLogger(__name__)

# Numeric Priority Weights for Policy Sorting (IMMEDIATE > HIGH > NORMAL)
PRIORITY_WEIGHTS: Dict[str, int] = {
    "IMMEDIATE": 3,
    "HIGH": 2,
    "NORMAL": 1,
}


class SelectionStrategy:
    """
    Implements rule selection policy, cross-aspect querying, deduplication, and priority ordering.
    """

    def __init__(self):
        logger.info("Initializing SelectionStrategy component")

    def select_recommendations(
        self, context: RecommendationContext, knowledge_base: RecommendationKnowledgeBase
    ) -> SelectionResult:
        """
        Executes selection strategy pipeline given context and knowledge base.
        
        :param context: Interpreted RecommendationContext.
        :param knowledge_base: Initialized RecommendationKnowledgeBase facade.
        :return: Immutable SelectionResult.
        """
        if not context or not getattr(context, "business_risk_result", None):
            raise SelectionValidationError("Invalid or null RecommendationContext supplied to SelectionStrategy.")

        logger.info("Starting recommendation rule selection strategy...")
        candidates: List[SelectedRecommendation] = []

        # 1. Primary & Secondary Aspect Queries
        if context.main_issue:
            candidates.extend(self._select_primary(context, knowledge_base))
        
        # 2. General Maintenance & Status Queries
        candidates.extend(self._select_general(context, knowledge_base))

        if not candidates:
            raise SelectionFailedError(
                f"No matching recommendation rules could be selected for context priority '{context.priority}'"
            )

        # 3. Apply Deduplication Filter across all merged queries
        unique_candidates = DeduplicationFilter.filter(candidates)

        # 4. Apply Selection Policy Priority Sorting (IMMEDIATE -> HIGH -> NORMAL)
        ordered_candidates = self._sort_by_priority(unique_candidates)

        # Determine highest priority among selected
        highest_priority = ordered_candidates[0].priority if ordered_candidates else context.priority

        logger.info(
            f"Selection strategy completed successfully. Selected {len(ordered_candidates)} rules. "
            f"Highest Priority: {highest_priority}"
        )

        return SelectionResult(
            selected=tuple(ordered_candidates),
            highest_priority=highest_priority,
            recommendation_count=len(ordered_candidates)
        )

    def _select_primary(
        self, context: RecommendationContext, knowledge_base: RecommendationKnowledgeBase
    ) -> List[SelectedRecommendation]:
        """
        Private helper querying primary and secondary aspect-specific candidate rules.
        """
        items: List[SelectedRecommendation] = []

        # Primary Aspect Query
        if context.main_issue:
            aspect = context.main_issue.upper()
            # Determine appropriate risk level for query from summary or result
            risk_level = str(context.risk_summary.get("highestRiskLevel", "HIGH")).upper()
            rules = knowledge_base.get_rules(aspect=aspect, risk_level=risk_level)

            # Fallback if specific level returned no rules
            if not rules:
                rules = knowledge_base.get_rules(aspect=aspect, risk_level="HIGH") or knowledge_base.get_rules(aspect=aspect, risk_level="MEDIUM")

            for r in rules:
                items.append(SelectedRecommendation(
                    aspect=aspect,
                    risk_level=r.risk_level,
                    rule=r,
                    priority=r.priority
                ))

        # Secondary Aspect Query
        if context.secondary_issue:
            sec_aspect = context.secondary_issue.upper()
            sec_rules = knowledge_base.get_rules(aspect=sec_aspect, risk_level="HIGH") or knowledge_base.get_rules(aspect=sec_aspect, risk_level="MEDIUM")
            
            for r in sec_rules:
                items.append(SelectedRecommendation(
                    aspect=sec_aspect,
                    risk_level=r.risk_level,
                    rule=r,
                    priority=r.priority
                ))

        return items

    def _select_general(
        self, context: RecommendationContext, knowledge_base: RecommendationKnowledgeBase
    ) -> List[SelectedRecommendation]:
        """
        Private helper querying general operational maintenance candidate rules based on business status.
        """
        items: List[SelectedRecommendation] = []
        status = str(context.interpreted_risks.get("businessStatus", "HEALTHY")).upper()

        # Map business status to general risk level query
        if status in ["CRITICAL", "HIGH"]:
            gen_risk = "HIGH"
        elif status in ["WARNING", "MEDIUM"]:
            gen_risk = "MEDIUM"
        else:
            gen_risk = "LOW"

        gen_rules = knowledge_base.get_general_rules(risk_level=gen_risk)
        if not gen_rules and gen_risk != "LOW":
            gen_rules = knowledge_base.get_general_rules(risk_level="LOW")

        for r in gen_rules:
            items.append(SelectedRecommendation(
                aspect="GENERAL",
                risk_level=r.risk_level,
                rule=r,
                priority=r.priority
            ))

        return items

    def _sort_by_priority(self, candidates: List[SelectedRecommendation]) -> List[SelectedRecommendation]:
        """
        Sorts candidates descending by numeric priority weight (IMMEDIATE = 3, HIGH = 2, NORMAL = 1).
        """
        def get_prio_weight(item: SelectedRecommendation) -> int:
            prio_str = str(item.priority).upper()
            return PRIORITY_WEIGHTS.get(prio_str, 1)

        return sorted(candidates, key=get_prio_weight, reverse=True)

"""
Knowledge Repository Component.
Provides indexed in-memory storage and defensive lookup for RecommendationRule objects.
"""

import logging
from typing import Dict, List, Optional
from core.recommendation.knowledge.models import RecommendationRule

logger = logging.getLogger(__name__)


class KnowledgeRepository:
    """
    In-memory storage and dual-indexed search engine for RecommendationRules.
    Guarantees thread-safe defensive copying for all query results.
    """

    def __init__(self):
        logger.info("Initializing KnowledgeRepository component")
        self._aspect_risk_index: Dict[str, Dict[str, List[RecommendationRule]]] = {}
        self._id_index: Dict[str, RecommendationRule] = {}
        self._all_rules: List[RecommendationRule] = []

    def build_indexes(self, rules: List[RecommendationRule]) -> None:
        """
        Builds primary dual indexes (Aspect -> RiskLevel -> Rules) and (RuleID -> Rule).
        
        :param rules: List of validated RecommendationRule objects.
        """
        logger.info(f"Building repository indexes for {len(rules)} recommendation rules...")
        self._aspect_risk_index.clear()
        self._id_index.clear()
        self._all_rules = list(rules)

        for rule in rules:
            self._id_index[rule.id] = rule

            aspect = rule.aspect.upper()
            risk = rule.risk_level.upper()

            if aspect not in self._aspect_risk_index:
                self._aspect_risk_index[aspect] = {}

            if risk not in self._aspect_risk_index[aspect]:
                self._aspect_risk_index[aspect][risk] = []

            self._aspect_risk_index[aspect][risk].append(rule)

        logger.info("Repository indexing completed successfully.")

    def find_rules(
        self,
        aspect: str,
        risk_level: str,
        priority: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[RecommendationRule]:
        """
        Finds matching enabled rules for aspect and risk level with defensive list copying.
        Supports optional priority and ANY-match tag filtering.
        """
        asp_key = str(aspect).upper()
        risk_key = str(risk_level).upper()

        matching = self._aspect_risk_index.get(asp_key, {}).get(risk_key, [])

        # Filter enabled rules first
        filtered: List[RecommendationRule] = [r for r in matching if r.enabled]

        # Optional Priority Filter
        if priority:
            prio_key = str(priority).upper()
            filtered = [r for r in filtered if r.priority.upper() == prio_key]

        # Optional Tag Filter (ANY-match logic)
        if tags and len(tags) > 0:
            query_tags = {str(t).lower() for t in tags}
            filtered = [
                r for r in filtered
                if any(str(rt).lower() in query_tags for rt in r.tags)
            ]

        # Return defensive copy
        return list(filtered)

    def get_by_id(self, rule_id: str) -> Optional[RecommendationRule]:
        """
        Looks up rule by unique rule ID from secondary index.
        """
        rule = self._id_index.get(rule_id)
        if rule and rule.enabled:
            return rule
        return None

    def get_all(self) -> List[RecommendationRule]:
        """
        Returns defensive copy list of all enabled rules.
        """
        return [r for r in self._all_rules if r.enabled]

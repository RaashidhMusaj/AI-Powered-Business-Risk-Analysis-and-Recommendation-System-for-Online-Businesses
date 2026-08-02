"""
Knowledge Validator Component.
Validates RecommendationRule schemas, unique IDs, aspect types, and risk levels.
"""

import logging
from typing import List, Set

from core.recommendation.constants.aspects import VALID_ASPECTS
from core.recommendation.constants.priorities import VALID_PRIORITIES
from core.recommendation.constants.risk_levels import VALID_RISK_LEVELS
from core.recommendation.knowledge.models import RecommendationRule
from core.recommendation.knowledge.exceptions import KnowledgeValidationError

logger = logging.getLogger(__name__)


class KnowledgeValidator:
    """
    Validates loaded RecommendationRule objects for schema and domain constraints.
    """

    def __init__(self):
        logger.info("Initializing KnowledgeValidator component")

    def validate_rules(self, rules: List[RecommendationRule]) -> None:
        """
        Validates a collection of rules for schema compliance and uniqueness.
        
        :param rules: List of RecommendationRule objects to validate.
        :raises KnowledgeValidationError: If any rule fails validation constraints.
        """
        logger.info(f"Validating {len(rules)} recommendation rules...")
        seen_ids: Set[str] = set()

        for rule in rules:
            self.validate_rule(rule)

            if rule.id in seen_ids:
                raise KnowledgeValidationError(f"Duplicate recommendation rule ID detected: '{rule.id}'")
            seen_ids.add(rule.id)

        logger.info("All recommendation rules passed validation successfully.")

    def validate_rule(self, rule: RecommendationRule) -> None:
        """
        Validates individual rule fields against domain contracts.
        """
        if not rule.id or not isinstance(rule.id, str) or not rule.id.strip():
            raise KnowledgeValidationError("Recommendation rule 'id' must be a non-empty string.")

        if rule.aspect not in VALID_ASPECTS:
            raise KnowledgeValidationError(
                f"Rule '{rule.id}' has invalid aspect '{rule.aspect}'. Valid aspects: {VALID_ASPECTS}"
            )

        if rule.risk_level not in VALID_RISK_LEVELS:
            raise KnowledgeValidationError(
                f"Rule '{rule.id}' has invalid risk level '{rule.risk_level}'. Valid levels: {VALID_RISK_LEVELS}"
            )

        if not rule.title or not isinstance(rule.title, str) or not rule.title.strip():
            raise KnowledgeValidationError(f"Rule '{rule.id}' must have a non-empty 'title'.")

        if not rule.description or not isinstance(rule.description, str) or not rule.description.strip():
            raise KnowledgeValidationError(f"Rule '{rule.id}' must have a non-empty 'description'.")

        if not rule.actions or not isinstance(rule.actions, (list, tuple)) or len(rule.actions) == 0:
            raise KnowledgeValidationError(f"Rule '{rule.id}' must have a non-empty 'actions' list.")

        for act in rule.actions:
            if not isinstance(act, str) or not act.strip():
                raise KnowledgeValidationError(f"Rule '{rule.id}' contains invalid empty action item.")

        if rule.priority not in VALID_PRIORITIES:
            raise KnowledgeValidationError(
                f"Rule '{rule.id}' has invalid priority '{rule.priority}'. Valid priorities: {VALID_PRIORITIES}"
            )

        if not isinstance(rule.tags, (list, tuple)):
            raise KnowledgeValidationError(f"Rule '{rule.id}' 'tags' must be a list or tuple of strings.")

        for tag in rule.tags:
            if not isinstance(tag, str):
                raise KnowledgeValidationError(f"Rule '{rule.id}' contains non-string tag: {tag}")

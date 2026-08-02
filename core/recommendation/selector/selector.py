"""
Action Selector Public Facade Component.
Exposes lean, single-entrypoint API for rule selection.
"""

import logging
from typing import Optional

from core.recommendation.dto.recommendation_context import RecommendationContext
from core.recommendation.knowledge.knowledge_base import RecommendationKnowledgeBase
from core.recommendation.selector.models import SelectionResult
from core.recommendation.selector.strategy import SelectionStrategy
from core.recommendation.selector.exceptions import SelectionError

logger = logging.getLogger(__name__)


class ActionSelector:
    """
    Public facade for the Action Selector component.
    Orchestrates selection strategy and knowledge base querying via dependency injection.
    Stateless and thread-safe for multi-tenant executions.
    """

    def __init__(
        self,
        knowledge_base: Optional[RecommendationKnowledgeBase] = None,
        strategy: Optional[SelectionStrategy] = None,
    ):
        """
        Initializes ActionSelector with optional knowledge base and strategy dependencies.
        """
        logger.info("Initializing ActionSelector facade instance")
        self.knowledge_base = knowledge_base
        self.strategy = strategy or SelectionStrategy()

    def select(self, context: RecommendationContext) -> SelectionResult:
        """
        Selects the best recommendation rules for the given RecommendationContext.
        Single public entrypoint for the selector component.
        
        :param context: Interpreted RecommendationContext object.
        :return: Immutable SelectionResult object.
        :raises SelectionError: If KnowledgeBase is uninitialized or selection fails.
        """
        logger.info(f"ActionSelector.select() called for context with priority '{getattr(context, 'priority', 'UNKNOWN')}'")

        kb = self.knowledge_base
        if not kb:
            # Fallback to initializing default RecommendationKnowledgeBase instance
            kb = RecommendationKnowledgeBase()
            kb.initialize()

        return self.strategy.select_recommendations(context, kb)

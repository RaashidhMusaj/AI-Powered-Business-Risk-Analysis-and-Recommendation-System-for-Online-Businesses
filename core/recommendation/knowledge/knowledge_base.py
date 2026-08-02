"""
Recommendation Knowledge Base Public Facade.
Provides centralized access to recommendation rule catalog with lazy initialization protection.
"""

import logging
from pathlib import Path
from typing import List, Optional, Union

from core.recommendation.knowledge.models import RecommendationRule
from core.recommendation.knowledge.exceptions import KnowledgeBaseError
from core.recommendation.knowledge.loader import KnowledgeLoader
from core.recommendation.knowledge.validator import KnowledgeValidator
from core.recommendation.knowledge.repository import KnowledgeRepository

logger = logging.getLogger(__name__)

# Default location for recommendation JSON data files
DEFAULT_DATA_DIR = Path(__file__).parent / "data"


class RecommendationKnowledgeBase:
    """
    Public entrypoint for the Recommendation Knowledge Base.
    Encapsulates Loader, Validator, and Repository behind a read-only query facade.
    Thread-safe and protected by initialization guards.
    """

    def __init__(
        self,
        loader: Optional[KnowledgeLoader] = None,
        validator: Optional[KnowledgeValidator] = None,
        repository: Optional[KnowledgeRepository] = None,
    ):
        logger.info("Initializing RecommendationKnowledgeBase facade instance")
        self.loader = loader or KnowledgeLoader()
        self.validator = validator or KnowledgeValidator()
        self.repository = repository or KnowledgeRepository()
        self._initialized: bool = False

    def initialize(self, data_dir: Optional[Union[str, Path]] = None) -> None:
        """
        Loads, validates, and indexes knowledge base rules from JSON files.
        
        :param data_dir: Optional custom data directory path. Defaults to internal data/ folder.
        """
        target_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        logger.info(f"Initializing Knowledge Base from directory: {target_dir}")

        rules = self.loader.load_all(target_dir)
        self.validator.validate_rules(rules)
        self.repository.build_indexes(rules)
        self._initialized = True

        logger.info("Recommendation Knowledge Base initialized successfully.")

    def _ensure_initialized(self) -> None:
        """
        Guard method enforcing initialization before querying.
        """
        if not self._initialized:
            raise KnowledgeBaseError(
                "RecommendationKnowledgeBase has not been initialized. Call initialize() before querying rules."
            )

    def get_rules(
        self,
        aspect: str,
        risk_level: str,
        priority: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[RecommendationRule]:
        """
        Retrieves matching recommendation rules for aspect and risk level.
        Returns a defensive list copy.
        """
        self._ensure_initialized()
        return self.repository.find_rules(aspect=aspect, risk_level=risk_level, priority=priority, tags=tags)

    def get_general_rules(self, risk_level: str) -> List[RecommendationRule]:
        """
        Shortcut for retrieving general recommendation rules.
        """
        self._ensure_initialized()
        return self.repository.find_rules(aspect="GENERAL", risk_level=risk_level)

    def get_rule_by_id(self, rule_id: str) -> Optional[RecommendationRule]:
        """
        Looks up a specific rule by ID.
        """
        self._ensure_initialized()
        return self.repository.get_by_id(rule_id)

    def get_all_rules(self) -> List[RecommendationRule]:
        """
        Retrieves all enabled rules in the Knowledge Base.
        """
        self._ensure_initialized()
        return self.repository.get_all()

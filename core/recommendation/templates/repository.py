"""
Template Repository Component.
Provides indexed in-memory storage and defensive lookup for RecommendationTemplate objects.
"""

import logging
from typing import Dict, List, Optional
from core.recommendation.templates.models import RecommendationTemplate

logger = logging.getLogger(__name__)


class TemplateRepository:
    """
    In-memory storage and dual-indexed search engine for RecommendationTemplates.
    Guarantees thread-safe defensive copying for all query results.
    """

    def __init__(self):
        logger.info("Initializing TemplateRepository component")
        self._category_id_index: Dict[str, Dict[str, RecommendationTemplate]] = {}
        self._id_index: Dict[str, RecommendationTemplate] = {}
        self._all_templates: List[RecommendationTemplate] = []

    def build_indexes(self, templates: List[RecommendationTemplate]) -> None:
        """
        Builds primary dual indexes (Category -> ID -> Template) and (ID -> Template).
        
        :param templates: List of validated RecommendationTemplate objects.
        """
        logger.info(f"Building repository indexes for {len(templates)} recommendation templates...")
        self._category_id_index.clear()
        self._id_index.clear()
        self._all_templates = list(templates)

        for tmpl in templates:
            self._id_index[tmpl.id] = tmpl

            cat = tmpl.category.upper()
            if cat not in self._category_id_index:
                self._category_id_index[cat] = {}

            self._category_id_index[cat][tmpl.id] = tmpl

        logger.info("Template repository indexing completed successfully.")

    def get_by_id(self, template_id: str) -> Optional[RecommendationTemplate]:
        """
        Looks up template by unique ID from secondary index.
        Returns template if enabled, otherwise None.
        """
        tmpl = self._id_index.get(template_id)
        if tmpl and tmpl.enabled:
            return tmpl
        return None

    def get_by_category(self, category: str) -> List[RecommendationTemplate]:
        """
        Returns defensive copy list of enabled templates for a specific category.
        """
        cat_key = str(category).upper()
        cat_dict = self._category_id_index.get(cat_key, {})
        return [tmpl for tmpl in cat_dict.values() if tmpl.enabled]

    def get_all(self) -> List[RecommendationTemplate]:
        """
        Returns defensive copy list of all enabled templates.
        """
        return [tmpl for tmpl in self._all_templates if tmpl.enabled]

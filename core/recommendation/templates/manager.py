"""
Template Manager Public Facade.
Provides centralized access to recommendation formatting templates with lazy initialization protection.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

from core.recommendation.templates.models import RecommendationTemplate
from core.recommendation.templates.exceptions import TemplateError, TemplateNotFoundError
from core.recommendation.templates.loader import TemplateLoader
from core.recommendation.templates.validator import TemplateValidator
from core.recommendation.templates.repository import TemplateRepository
from core.recommendation.templates.renderer import TemplateRenderer

logger = logging.getLogger(__name__)

# Default location for template JSON data files
DEFAULT_DATA_DIR = Path(__file__).parent / "data"


class TemplateManager:
    """
    Public entrypoint facade for the Recommendation Template System.
    Encapsulates Loader, Validator, Repository, and Renderer behind a clean formatting interface.
    Thread-safe and protected by initialization guards.
    """

    def __init__(
        self,
        loader: Optional[TemplateLoader] = None,
        validator: Optional[TemplateValidator] = None,
        repository: Optional[TemplateRepository] = None,
        renderer: Optional[TemplateRenderer] = None,
    ):
        logger.info("Initializing TemplateManager facade instance")
        self.loader = loader or TemplateLoader()
        self.validator = validator or TemplateValidator()
        self.repository = repository or TemplateRepository()
        self.renderer = renderer or TemplateRenderer()
        self._initialized: bool = False

    def initialize(self, data_dir: Optional[Union[str, Path]] = None) -> None:
        """
        Loads, validates, and indexes template rules from JSON files.
        
        :param data_dir: Optional custom data directory path. Defaults to internal data/ folder.
        """
        target_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        logger.info(f"Initializing Template Manager from directory: {target_dir}")

        templates = self.loader.load_all(target_dir)
        self.validator.validate_templates(templates)
        self.repository.build_indexes(templates)
        self._initialized = True

        logger.info("Template Manager initialized successfully.")

    def _ensure_initialized(self) -> None:
        """
        Guard method enforcing initialization before rendering or querying.
        """
        if not self._initialized:
            raise TemplateError(
                "TemplateManager has not been initialized. Call initialize() before rendering templates."
            )

    def render(self, template_id: str, values: Optional[Dict[str, Any]] = None) -> str:
        """
        Core generic method rendering any template by ID.
        
        :param template_id: Unique template identifier.
        :param values: Optional dictionary of placeholder replacement values.
        :return: Formatted text string.
        """
        self._ensure_initialized()
        template = self.repository.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(f"Template with ID '{template_id}' not found or is disabled.")

        return self.renderer.render(template, values or {})

    def render_summary(self, template_id: str, values: Optional[Dict[str, Any]] = None) -> str:
        """
        Convenience wrapper rendering summary template.
        """
        return self.render(template_id, values)

    def render_insight(self, template_id: str, values: Optional[Dict[str, Any]] = None) -> str:
        """
        Convenience wrapper rendering insight template.
        """
        return self.render(template_id, values)

    def render_action(self, template_id: str, values: Optional[Dict[str, Any]] = None) -> str:
        """
        Convenience wrapper rendering action template.
        """
        return self.render(template_id, values)

    def get_template(self, template_id: str) -> Optional[RecommendationTemplate]:
        """
        Looks up a specific template by ID.
        """
        self._ensure_initialized()
        return self.repository.get_by_id(template_id)

    def get_all_templates(self) -> List[RecommendationTemplate]:
        """
        Retrieves all enabled templates.
        """
        self._ensure_initialized()
        return self.repository.get_all()

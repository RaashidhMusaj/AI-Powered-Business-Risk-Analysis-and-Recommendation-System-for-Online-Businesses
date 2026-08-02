"""
Template Renderer Component.
Safely formats RecommendationTemplate text strings using supplied values map.
"""

import logging
from typing import Dict, Any, Optional

from core.recommendation.templates.models import RecommendationTemplate
from core.recommendation.templates.exceptions import TemplateRenderingError

logger = logging.getLogger(__name__)


class TemplateRenderer:
    """
    Stateless renderer replacing placeholders in RecommendationTemplate strings.
    """

    def __init__(self):
        logger.info("Initializing TemplateRenderer component")

    def render(self, template: RecommendationTemplate, values: Optional[Dict[str, Any]] = None) -> str:
        """
        Renders template text by replacing declared placeholders with values.
        
        :param template: RecommendationTemplate instance.
        :param values: Dictionary containing values for template placeholders.
        :return: Rendered text string.
        :raises TemplateRenderingError: If required placeholder values are missing or syntax is invalid.
        """
        val_map = values or {}

        # Validate that all declared placeholders are supplied
        missing_keys = [ph for ph in template.placeholders if ph not in val_map]
        if missing_keys:
            raise TemplateRenderingError(
                f"Missing required placeholder value(s) {missing_keys} for template '{template.id}'"
            )

        try:
            rendered_text = template.template.format(**val_map)
            return rendered_text
        except KeyError as ke:
            raise TemplateRenderingError(f"Missing placeholder key {ke} during rendering of template '{template.id}'")
        except (ValueError, IndexError) as ve:
            raise TemplateRenderingError(f"Invalid formatting syntax in template '{template.id}': {str(ve)}")
        except Exception as ex:
            raise TemplateRenderingError(f"Unexpected error rendering template '{template.id}': {str(ex)}")

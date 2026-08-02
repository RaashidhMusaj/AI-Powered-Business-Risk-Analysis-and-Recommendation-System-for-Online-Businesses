"""
Template Validator Component.
Validates RecommendationTemplate schemas, categories, unique IDs, and placeholder syntax.
"""

import logging
from typing import List, Set

from core.recommendation.constants.template_categories import VALID_TEMPLATE_CATEGORIES
from core.recommendation.templates.models import RecommendationTemplate
from core.recommendation.templates.exceptions import TemplateValidationError

logger = logging.getLogger(__name__)


class TemplateValidator:
    """
    Validates loaded RecommendationTemplate objects for schema and category constraints.
    """

    def __init__(self):
        logger.info("Initializing TemplateValidator component")

    def validate_templates(self, templates: List[RecommendationTemplate]) -> None:
        """
        Validates a collection of templates for schema compliance and ID uniqueness.
        
        :param templates: List of RecommendationTemplate objects to validate.
        :raises TemplateValidationError: If any template fails validation constraints.
        """
        logger.info(f"Validating {len(templates)} recommendation templates...")
        seen_ids: Set[str] = set()

        for template in templates:
            self.validate_template(template)

            if template.id in seen_ids:
                raise TemplateValidationError(f"Duplicate recommendation template ID detected: '{template.id}'")
            seen_ids.add(template.id)

        logger.info("All recommendation templates passed validation successfully.")

    def validate_template(self, template: RecommendationTemplate) -> None:
        """
        Validates individual template fields against domain contracts.
        """
        if not template.id or not isinstance(template.id, str) or not template.id.strip():
            raise TemplateValidationError("Recommendation template 'id' must be a non-empty string.")

        if template.category not in VALID_TEMPLATE_CATEGORIES:
            raise TemplateValidationError(
                f"Template '{template.id}' has invalid category '{template.category}'. "
                f"Valid categories: {VALID_TEMPLATE_CATEGORIES}"
            )

        if not template.template or not isinstance(template.template, str) or not template.template.strip():
            raise TemplateValidationError(f"Template '{template.id}' must have a non-empty 'template' text string.")

        if not isinstance(template.placeholders, (list, tuple)):
            raise TemplateValidationError(f"Template '{template.id}' 'placeholders' must be a list or tuple of strings.")

        for ph in template.placeholders:
            if not isinstance(ph, str) or not ph.strip():
                raise TemplateValidationError(f"Template '{template.id}' contains invalid empty placeholder item.")
            expected_token = "{" + ph + "}"
            if expected_token not in template.template:
                raise TemplateValidationError(
                    f"Template '{template.id}' declares placeholder '{ph}', but '{expected_token}' is not in template text."
                )

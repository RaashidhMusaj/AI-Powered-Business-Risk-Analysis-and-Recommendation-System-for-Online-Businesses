"""
Template Loader Component.
Reads and parses JSON template files with deterministic cross-platform file sorting.
"""

import json
import logging
from pathlib import Path
from typing import List, Union

from core.recommendation.templates.models import RecommendationTemplate
from core.recommendation.templates.exceptions import TemplateNotFoundError, TemplateValidationError

logger = logging.getLogger(__name__)


class TemplateLoader:
    """
    Loads JSON template files from disk into RecommendationTemplate instances.
    """

    def __init__(self):
        logger.info("Initializing TemplateLoader component")

    def load_all(self, data_dir: Union[str, Path]) -> List[RecommendationTemplate]:
        """
        Scans data directory, sorts JSON files deterministically, and loads all templates.
        
        :param data_dir: Directory containing JSON template files.
        :return: List of loaded RecommendationTemplate objects.
        """
        dir_path = Path(data_dir)
        if not dir_path.exists() or not dir_path.is_dir():
            raise TemplateNotFoundError(f"Template data directory not found: {dir_path}")

        # Deterministic sorting of JSON files, ignoring hidden files (starting with '.')
        json_files = sorted([
            f for f in dir_path.glob("*.json")
            if not f.name.startswith(".") and f.is_file()
        ])

        if not json_files:
            raise TemplateNotFoundError(f"No valid JSON template files found in directory: {dir_path}")

        logger.info(f"Loading {len(json_files)} template files from {dir_path}")

        all_templates: List[RecommendationTemplate] = []
        for file_path in json_files:
            templates = self.load_file(file_path)
            all_templates.extend(templates)

        logger.info(f"Successfully loaded {len(all_templates)} total recommendation templates.")
        return all_templates

    def load_file(self, file_path: Union[str, Path]) -> List[RecommendationTemplate]:
        """
        Reads and parses a single JSON template file into RecommendationTemplate instances.
        """
        path = Path(file_path)
        logger.info(f"Loading template file: {path.name}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise TemplateValidationError(f"Failed to read/parse JSON file '{path.name}': {str(e)}")

        if not isinstance(data, list):
            raise TemplateValidationError(f"Root structure in JSON file '{path.name}' must be a JSON Array.")

        templates: List[RecommendationTemplate] = []
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                raise TemplateValidationError(f"Entry #{index} in '{path.name}' is not a JSON Object.")

            try:
                placeholders = tuple(item.get("placeholders", [])) if isinstance(item.get("placeholders"), list) else ()

                template_obj = RecommendationTemplate(
                    id=str(item["id"]) if "id" in item else "",
                    category=str(item.get("category", "")).upper(),
                    template=str(item.get("template", "")),
                    placeholders=placeholders,
                    enabled=bool(item.get("enabled", True)),
                )
                templates.append(template_obj)
            except KeyError as ke:
                raise TemplateValidationError(f"Missing required field {ke} in '{path.name}' entry #{index}")
            except Exception as ex:
                raise TemplateValidationError(f"Invalid template format in '{path.name}' entry #{index}: {str(ex)}")

        return templates

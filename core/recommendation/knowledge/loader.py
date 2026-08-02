"""
Knowledge Loader Component.
Reads and parses JSON rule files with deterministic cross-platform file sorting.
"""

import json
import logging
from pathlib import Path
from typing import List, Union

from core.recommendation.knowledge.models import RecommendationRule
from core.recommendation.knowledge.exceptions import KnowledgeNotFoundError, KnowledgeValidationError

logger = logging.getLogger(__name__)


class KnowledgeLoader:
    """
    Loads JSON rule files from disk into RecommendationRule instances.
    """

    def __init__(self):
        logger.info("Initializing KnowledgeLoader component")

    def load_all(self, data_dir: Union[str, Path]) -> List[RecommendationRule]:
        """
        Scans data directory, sorts JSON files deterministically, and loads all rules.
        
        :param data_dir: Directory containing JSON knowledge rule files.
        :return: List of loaded RecommendationRule objects.
        """
        dir_path = Path(data_dir)
        if not dir_path.exists() or not dir_path.is_dir():
            raise KnowledgeNotFoundError(f"Knowledge base data directory not found: {dir_path}")

        # Deterministic sorting of JSON files, ignoring hidden files (starting with '.')
        json_files = sorted([
            f for f in dir_path.glob("*.json")
            if not f.name.startswith(".") and f.is_file()
        ])

        if not json_files:
            raise KnowledgeNotFoundError(f"No valid JSON knowledge files found in directory: {dir_path}")

        logger.info(f"Loading {len(json_files)} knowledge files from {dir_path}")

        all_rules: List[RecommendationRule] = []
        for file_path in json_files:
            rules = self.load_file(file_path)
            all_rules.extend(rules)

        logger.info(f"Successfully loaded {len(all_rules)} total recommendation rules.")
        return all_rules

    def load_file(self, file_path: Union[str, Path]) -> List[RecommendationRule]:
        """
        Reads and parses a single JSON rule file into RecommendationRule instances.
        """
        path = Path(file_path)
        logger.info(f"Loading knowledge file: {path.name}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise KnowledgeValidationError(f"Failed to read/parse JSON file '{path.name}': {str(e)}")

        if not isinstance(data, list):
            raise KnowledgeValidationError(f"Root structure in JSON file '{path.name}' must be a JSON Array.")

        rules: List[RecommendationRule] = []
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                raise KnowledgeValidationError(f"Entry #{index} in '{path.name}' is not a JSON Object.")

            try:
                actions = tuple(item.get("actions", [])) if isinstance(item.get("actions"), list) else ()
                tags = tuple(item.get("tags", [])) if isinstance(item.get("tags"), list) else ()

                rule = RecommendationRule(
                    id=str(item["id"]) if "id" in item else "",
                    aspect=str(item.get("aspect", "")).upper(),
                    risk_level=str(item.get("risk_level", "")).upper(),
                    title=str(item.get("title", "")),
                    description=str(item.get("description", "")),
                    actions=actions,
                    priority=str(item.get("priority", "HIGH")).upper(),
                    tags=tags,
                    version=int(item.get("version", 1)),
                    enabled=bool(item.get("enabled", True)),
                )
                rules.append(rule)
            except KeyError as ke:
                raise KnowledgeValidationError(f"Missing required field {ke} in '{path.name}' entry #{index}")
            except Exception as ex:
                raise KnowledgeValidationError(f"Invalid rule format in '{path.name}' entry #{index}: {str(ex)}")

        return rules

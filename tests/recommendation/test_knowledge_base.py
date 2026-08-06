"""
Unit Tests for Phase 3 – Recommendation Knowledge Base (RKB).
Verifies rule loading, validation, indexing, defensive copying, lazy initialization, and queries.
"""

import json
import pytest
from pathlib import Path
from dataclasses import FrozenInstanceError

from core.recommendation.knowledge.models import RecommendationRule
from core.recommendation.knowledge.exceptions import (
    KnowledgeBaseError,
    KnowledgeValidationError,
    KnowledgeNotFoundError,
)
from core.recommendation.knowledge.knowledge_base import RecommendationKnowledgeBase
from core.recommendation.knowledge.validator import KnowledgeValidator


@pytest.fixture
def knowledge_base() -> RecommendationKnowledgeBase:
    kb = RecommendationKnowledgeBase()
    kb.initialize()
    return kb


def test_scenario_1_valid_json_loading(knowledge_base: RecommendationKnowledgeBase):
    """
    Scenario 1: Valid JSON files load successfully and populate indexes.
    """
    all_rules = knowledge_base.get_all_rules()
    assert len(all_rules) >= 7

    quality_high = knowledge_base.get_rules("QUALITY", "HIGH")
    assert len(quality_high) >= 1
    assert quality_high[0].id == "quality_high_001"
    assert quality_high[0].aspect == "QUALITY"
    assert quality_high[0].risk_level == "HIGH"
    assert len(quality_high[0].actions) > 0


def test_scenario_2_duplicate_ids(tmp_path: Path):
    """
    Scenario 2: Duplicate rule IDs raise KnowledgeValidationError.
    """
    file_content = [
        {
            "id": "dup_001",
            "aspect": "QUALITY",
            "risk_level": "HIGH",
            "title": "Rule 1",
            "description": "Desc 1",
            "actions": ["Action 1"]
        },
        {
            "id": "dup_001",
            "aspect": "DELIVERY",
            "risk_level": "LOW",
            "title": "Rule 2",
            "description": "Desc 2",
            "actions": ["Action 2"]
        }
    ]
    json_file = tmp_path / "dup.json"
    json_file.write_text(json.dumps(file_content), encoding="utf-8")

    kb = RecommendationKnowledgeBase()
    with pytest.raises(KnowledgeValidationError) as exc_info:
        kb.initialize(data_dir=tmp_path)
    assert "Duplicate recommendation rule ID detected" in str(exc_info.value)


def test_scenario_3_missing_required_fields(tmp_path: Path):
    """
    Scenario 3: Missing required field raises KnowledgeValidationError.
    """
    file_content = [
        {
            "id": "missing_001",
            "aspect": "QUALITY",
            "risk_level": "HIGH",
            # missing 'title', 'description', 'actions'
        }
    ]
    json_file = tmp_path / "missing.json"
    json_file.write_text(json.dumps(file_content), encoding="utf-8")

    kb = RecommendationKnowledgeBase()
    with pytest.raises(KnowledgeValidationError):
        kb.initialize(data_dir=tmp_path)


def test_scenario_4_unknown_risk_level_or_aspect(tmp_path: Path):
    """
    Scenario 4: Unknown risk level or aspect raises KnowledgeValidationError.
    """
    file_content = [
        {
            "id": "invalid_001",
            "aspect": "INVALID_ASPECT",
            "risk_level": "UNKNOWN_LEVEL",
            "title": "Invalid Rule",
            "description": "Invalid Desc",
            "actions": ["Action 1"]
        }
    ]
    json_file = tmp_path / "invalid.json"
    json_file.write_text(json.dumps(file_content), encoding="utf-8")

    kb = RecommendationKnowledgeBase()
    with pytest.raises(KnowledgeValidationError) as exc_info:
        kb.initialize(data_dir=tmp_path)
    assert "invalid aspect" in str(exc_info.value).lower() or "invalid risk level" in str(exc_info.value).lower()


def test_scenario_5_lookup_and_defensive_copying(knowledge_base: RecommendationKnowledgeBase):
    """
    Scenario 5: Lookup returns matching collection and protects internal repository state.
    """
    rules = knowledge_base.get_rules("QUALITY", "HIGH")
    assert len(rules) > 0

    # Modify returned list defensively
    rules.clear()

    # Re-query should still return original rules intact
    fresh_rules = knowledge_base.get_rules("QUALITY", "HIGH")
    assert len(fresh_rules) > 0


def test_scenario_6_empty_directory(tmp_path: Path):
    """
    Scenario 6: Empty knowledge base directory raises KnowledgeNotFoundError.
    """
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()

    kb = RecommendationKnowledgeBase()
    with pytest.raises(KnowledgeNotFoundError):
        kb.initialize(data_dir=empty_dir)


def test_scenario_7_disabled_rule_filtering(tmp_path: Path):
    """
    Scenario 7: Rules with enabled=false are excluded from query results.
    """
    file_content = [
        {
            "id": "disabled_001",
            "aspect": "QUALITY",
            "risk_level": "HIGH",
            "title": "Disabled Rule",
            "description": "Disabled Desc",
            "actions": ["Action 1"],
            "enabled": False
        },
        {
            "id": "enabled_001",
            "aspect": "QUALITY",
            "risk_level": "HIGH",
            "title": "Enabled Rule",
            "description": "Enabled Desc",
            "actions": ["Action 2"],
            "enabled": True
        }
    ]
    json_file = tmp_path / "rules.json"
    json_file.write_text(json.dumps(file_content), encoding="utf-8")

    kb = RecommendationKnowledgeBase()
    kb.initialize(data_dir=tmp_path)

    rules = kb.get_rules("QUALITY", "HIGH")
    assert len(rules) == 1
    assert rules[0].id == "enabled_001"
    assert kb.get_rule_by_id("disabled_001") is None


def test_scenario_8_any_match_tag_filtering(knowledge_base: RecommendationKnowledgeBase):
    """
    Scenario 8: ANY-match tag filtering.
    """
    rules = knowledge_base.get_rules("QUALITY", "HIGH", tags=["product_quality", "non_existent_tag"])
    assert len(rules) >= 1
    assert rules[0].id == "quality_high_001"


def test_scenario_9_uninitialized_query_guard():
    """
    Scenario 9: Querying uninitialized KnowledgeBase raises KnowledgeBaseError.
    """
    uninitialized_kb = RecommendationKnowledgeBase()
    with pytest.raises(KnowledgeBaseError) as exc_info:
        uninitialized_kb.get_rules("QUALITY", "HIGH")
    assert "not been initialized" in str(exc_info.value).lower()


def test_scenario_10_rule_immutability(knowledge_base: RecommendationKnowledgeBase):
    """
    Scenario 10: Modifying frozen RecommendationRule attributes raises FrozenInstanceError.
    """
    rule = knowledge_base.get_rule_by_id("quality_high_001")
    assert rule is not None

    with pytest.raises(FrozenInstanceError):
        rule.title = "Modified Title"  # type: ignore

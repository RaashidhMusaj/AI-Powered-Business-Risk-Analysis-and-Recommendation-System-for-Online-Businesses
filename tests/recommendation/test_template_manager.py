"""
Unit Tests for Phase 4 – Template Manager.
Verifies loading, validation, repository indexing, rendering, syntax error handling, defensive copying, and guards.
"""

import json
import pytest
from pathlib import Path
from dataclasses import FrozenInstanceError

from core.recommendation.templates.models import RecommendationTemplate
from core.recommendation.templates.exceptions import (
    TemplateError,
    TemplateValidationError,
    TemplateNotFoundError,
    TemplateRenderingError,
)
from core.recommendation.templates.manager import TemplateManager


@pytest.fixture
def template_manager() -> TemplateManager:
    tm = TemplateManager()
    tm.initialize()
    return tm


def test_scenario_1_valid_templates_loading(template_manager: TemplateManager):
    """
    Scenario 1: Valid templates load successfully into manager.
    """
    all_tmpls = template_manager.get_all_templates()
    assert len(all_tmpls) >= 9

    summary_tmpl = template_manager.get_template("summary_high_quality")
    assert summary_tmpl is not None
    assert summary_tmpl.category == "SUMMARY"
    assert "aspect" in summary_tmpl.placeholders


def test_scenario_2_duplicate_template_ids(tmp_path: Path):
    """
    Scenario 2: Duplicate template IDs raise TemplateValidationError.
    """
    file_content = [
        {
            "id": "dup_001",
            "category": "SUMMARY",
            "template": "Summary {aspect}",
            "placeholders": ["aspect"]
        },
        {
            "id": "dup_001",
            "category": "INSIGHT",
            "template": "Insight text",
            "placeholders": []
        }
    ]
    json_file = tmp_path / "dup.json"
    json_file.write_text(json.dumps(file_content), encoding="utf-8")

    tm = TemplateManager()
    with pytest.raises(TemplateValidationError) as exc_info:
        tm.initialize(data_dir=tmp_path)
    assert "Duplicate recommendation template ID detected" in str(exc_info.value)


def test_scenario_3_missing_declared_placeholders(tmp_path: Path):
    """
    Scenario 3: Declared placeholders missing from template string raise TemplateValidationError.
    """
    file_content = [
        {
            "id": "missing_ph_001",
            "category": "SUMMARY",
            "template": "Summary without placeholders in text",
            "placeholders": ["declared_but_missing"]
        }
    ]
    json_file = tmp_path / "missing_ph.json"
    json_file.write_text(json.dumps(file_content), encoding="utf-8")

    tm = TemplateManager()
    with pytest.raises(TemplateValidationError) as exc_info:
        tm.initialize(data_dir=tmp_path)
    assert "declares placeholder" in str(exc_info.value)


def test_scenario_4_unknown_template_category(tmp_path: Path):
    """
    Scenario 4: Unknown template category raises TemplateValidationError.
    """
    file_content = [
        {
            "id": "bad_cat_001",
            "category": "INVALID_CATEGORY",
            "template": "Text",
            "placeholders": []
        }
    ]
    json_file = tmp_path / "bad_cat.json"
    json_file.write_text(json.dumps(file_content), encoding="utf-8")

    tm = TemplateManager()
    with pytest.raises(TemplateValidationError) as exc_info:
        tm.initialize(data_dir=tmp_path)
    assert "invalid category" in str(exc_info.value).lower()


def test_scenario_5_successful_placeholder_rendering(template_manager: TemplateManager):
    """
    Scenario 5: Placeholder rendering produces expected formatted output.
    """
    rendered = template_manager.render_summary("summary_high_quality", {"aspect": "Product Quality"})
    assert "Product Quality" in rendered
    assert "Our analysis" in rendered


def test_scenario_6_missing_placeholder_runtime_value(template_manager: TemplateManager):
    """
    Scenario 6: Missing placeholder value at runtime raises TemplateRenderingError.
    """
    with pytest.raises(TemplateRenderingError) as exc_info:
        template_manager.render_summary("summary_high_quality", {})
    assert "Missing required placeholder value" in str(exc_info.value)


def test_scenario_7_disabled_template_exclusion(tmp_path: Path):
    """
    Scenario 7: Disabled templates are excluded from rendering and queries.
    """
    file_content = [
        {
            "id": "disabled_001",
            "category": "SUMMARY",
            "template": "Text",
            "placeholders": [],
            "enabled": False
        }
    ]
    json_file = tmp_path / "disabled.json"
    json_file.write_text(json.dumps(file_content), encoding="utf-8")

    tm = TemplateManager()
    tm.initialize(data_dir=tmp_path)

    assert tm.get_template("disabled_001") is None
    with pytest.raises(TemplateNotFoundError):
        tm.render("disabled_001")


def test_scenario_8_uninitialized_manager_guard():
    """
    Scenario 8: Uninitialized TemplateManager raises TemplateError.
    """
    uninit_tm = TemplateManager()
    with pytest.raises(TemplateError) as exc_info:
        uninit_tm.render("summary_high_quality")
    assert "has not been initialized" in str(exc_info.value).lower()


def test_scenario_9_defensive_copies(template_manager: TemplateManager):
    """
    Scenario 9: Defensive copying protects repository state.
    """
    tmpls = template_manager.get_all_templates()
    tmpls.clear()

    fresh_tmpls = template_manager.get_all_templates()
    assert len(fresh_tmpls) >= 9


def test_scenario_10_invalid_formatting_syntax(tmp_path: Path):
    """
    Scenario 10: Invalid formatting syntax (e.g. unclosed brace '{aspect') raises TemplateRenderingError.
    """
    # Bypass validator to test renderer syntax failure handling directly
    from core.recommendation.templates.renderer import TemplateRenderer
    renderer = TemplateRenderer()
    broken_tmpl = RecommendationTemplate(
        id="broken_syntax_001",
        category="SUMMARY",
        template="Broken syntax {aspect",
        placeholders=("aspect",)
    )

    with pytest.raises(TemplateRenderingError) as exc_info:
        renderer.render(broken_tmpl, {"aspect": "Quality"})
    assert "Invalid formatting syntax" in str(exc_info.value)

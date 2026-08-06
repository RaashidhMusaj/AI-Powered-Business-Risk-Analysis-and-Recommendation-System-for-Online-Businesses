"""
Unit Tests for Phase 6 – Report Builder Component.
Verifies report validation, template resolution, section assembly, metadata propagation, order preservation, and immutability.
"""

import pytest
from datetime import datetime
from dataclasses import FrozenInstanceError
from unittest.mock import MagicMock

from core.recommendation.knowledge.models import RecommendationRule
from core.recommendation.templates.manager import TemplateManager
from core.recommendation.templates.exceptions import TemplateRenderingError
from core.recommendation.selector.models import SelectionResult, SelectedRecommendation

from core.recommendation.report.models import RecommendationReport
from core.recommendation.report.builder import ReportBuilder
from core.recommendation.report.assembler import ReportAssembler
from core.recommendation.report.exceptions import (
    ReportError,
    ReportValidationError,
    ReportBuildError,
)


@pytest.fixture
def template_manager() -> TemplateManager:
    tm = TemplateManager()
    tm.initialize()
    return tm


@pytest.fixture
def report_builder(template_manager: TemplateManager) -> ReportBuilder:
    return ReportBuilder(template_manager=template_manager)


@pytest.fixture
def sample_rule_quality() -> RecommendationRule:
    return RecommendationRule(
        id="quality_high_001",
        aspect="QUALITY",
        risk_level="HIGH",
        title="Resolve Major Quality Issues",
        description="Inspect stock for defects.",
        actions=("Inspect product stock", "Halt defective batches"),
        priority="IMMEDIATE"
    )


@pytest.fixture
def sample_rule_delivery() -> RecommendationRule:
    return RecommendationRule(
        id="delivery_medium_001",
        aspect="DELIVERY",
        risk_level="MEDIUM",
        title="Improve Delivery Efficiency",
        description="Optimize shipping dispatch time.",
        actions=("Dispatch orders quickly", "Set accurate delivery dates"),
        priority="HIGH"
    )


@pytest.fixture
def sample_rule_general() -> RecommendationRule:
    return RecommendationRule(
        id="general_low_001",
        aspect="GENERAL",
        risk_level="LOW",
        title="Keep Up Performance",
        description="Maintain current service standards.",
        actions=("Monitor feedback", "Respond promptly"),
        priority="NORMAL"
    )


def test_scenario_1_high_risk_product_report(report_builder: ReportBuilder, sample_rule_quality: RecommendationRule):
    """
    Scenario 1: High-risk product generates executive summary, insights, actions, and metadata.
    """
    selected_item = SelectedRecommendation(
        aspect="QUALITY",
        risk_level="HIGH",
        rule=sample_rule_quality,
        priority="IMMEDIATE"
    )
    selection_result = SelectionResult(
        selected=(selected_item,),
        highest_priority="IMMEDIATE",
        recommendation_count=1
    )

    report = report_builder.build(selection_result)

    assert isinstance(report, RecommendationReport)
    assert len(report.summary) > 0
    assert len(report.insights) >= 1
    assert len(report.actions) >= 1
    assert report.highest_priority == "IMMEDIATE"
    assert report.recommendation_count == 1
    assert isinstance(report.generated_at, datetime)


def test_scenario_2_healthy_business_report(report_builder: ReportBuilder, sample_rule_general: RecommendationRule):
    """
    Scenario 2: Healthy business generates healthy summary and maintenance actions without warnings.
    """
    selected_item = SelectedRecommendation(
        aspect="GENERAL",
        risk_level="LOW",
        rule=sample_rule_general,
        priority="NORMAL"
    )
    selection_result = SelectionResult(
        selected=(selected_item,),
        highest_priority="NORMAL",
        recommendation_count=1
    )

    report = report_builder.build(selection_result)

    assert report.highest_priority == "NORMAL"
    assert "Monitor feedback" in report.actions or "Respond promptly" in report.actions


def test_scenario_3_multiple_recommendations_report(
    report_builder: ReportBuilder,
    sample_rule_quality: RecommendationRule,
    sample_rule_delivery: RecommendationRule
):
    """
    Scenario 3: Multiple recommendations include all insights and actions in priority order.
    """
    item1 = SelectedRecommendation(aspect="QUALITY", risk_level="HIGH", rule=sample_rule_quality, priority="IMMEDIATE")
    item2 = SelectedRecommendation(aspect="DELIVERY", risk_level="MEDIUM", rule=sample_rule_delivery, priority="HIGH")

    selection_result = SelectionResult(
        selected=(item1, item2),
        highest_priority="IMMEDIATE",
        recommendation_count=2
    )

    report = report_builder.build(selection_result)

    assert report.recommendation_count == 2
    assert len(report.insights) >= 2
    assert len(report.actions) >= 2


def test_scenario_4_empty_selection_result_raises_validation_error(report_builder: ReportBuilder):
    """
    Scenario 4: Null or empty SelectionResult raises ReportValidationError.
    """
    with pytest.raises(ReportValidationError):
        report_builder.build(None)  # type: ignore

    empty_selection = SelectionResult(selected=(), highest_priority="NORMAL", recommendation_count=0)
    with pytest.raises(ReportValidationError):
        report_builder.build(empty_selection)


def test_scenario_5_rendering_failure_raises_build_error(sample_rule_quality: RecommendationRule):
    """
    Scenario 5: Exception during assembly/rendering raises ReportBuildError.
    """
    mock_tm = MagicMock(spec=TemplateManager)
    mock_tm.render_summary.side_effect = TemplateRenderingError("Template rendering error")

    builder_instance = ReportBuilder(template_manager=mock_tm)

    selected_item = SelectedRecommendation(
        aspect="QUALITY",
        risk_level="HIGH",
        rule=sample_rule_quality,
        priority="IMMEDIATE"
    )
    selection_result = SelectionResult(
        selected=(selected_item,),
        highest_priority="IMMEDIATE",
        recommendation_count=1
    )

    with pytest.raises(ReportBuildError) as exc_info:
        builder_instance.build(selection_result)
    assert "Failed to assemble recommendation report" in str(exc_info.value)


def test_scenario_6_immutable_report(report_builder: ReportBuilder, sample_rule_quality: RecommendationRule):
    """
    Scenario 6: Modifying frozen RecommendationReport attributes raises FrozenInstanceError.
    """
    selected_item = SelectedRecommendation(aspect="QUALITY", risk_level="HIGH", rule=sample_rule_quality, priority="IMMEDIATE")
    selection_result = SelectionResult(selected=(selected_item,), highest_priority="IMMEDIATE", recommendation_count=1)

    report = report_builder.build(selection_result)

    with pytest.raises(FrozenInstanceError):
        report.summary = "New Summary"  # type: ignore


def test_scenario_7_highest_priority_propagation(report_builder: ReportBuilder, sample_rule_quality: RecommendationRule):
    """
    Scenario 7: SelectionResult.highest_priority is correctly propagated to RecommendationReport.
    """
    selected_item = SelectedRecommendation(aspect="QUALITY", risk_level="HIGH", rule=sample_rule_quality, priority="IMMEDIATE")
    selection_result = SelectionResult(selected=(selected_item,), highest_priority="IMMEDIATE", recommendation_count=1)

    report = report_builder.build(selection_result)
    assert report.highest_priority == selection_result.highest_priority


def test_scenario_8_recommendation_count_propagation(report_builder: ReportBuilder, sample_rule_quality: RecommendationRule):
    """
    Scenario 8: SelectionResult.recommendation_count is correctly propagated to RecommendationReport.
    """
    selected_item = SelectedRecommendation(aspect="QUALITY", risk_level="HIGH", rule=sample_rule_quality, priority="IMMEDIATE")
    selection_result = SelectionResult(selected=(selected_item,), highest_priority="IMMEDIATE", recommendation_count=1)

    report = report_builder.build(selection_result)
    assert report.recommendation_count == selection_result.recommendation_count


def test_scenario_9_section_structure_non_empty(report_builder: ReportBuilder, sample_rule_quality: RecommendationRule):
    """
    Scenario 9: Rendered content structure contains non-empty summary, insights, and actions.
    """
    selected_item = SelectedRecommendation(aspect="QUALITY", risk_level="HIGH", rule=sample_rule_quality, priority="IMMEDIATE")
    selection_result = SelectionResult(selected=(selected_item,), highest_priority="IMMEDIATE", recommendation_count=1)

    report = report_builder.build(selection_result)

    assert isinstance(report.summary, str) and len(report.summary) > 0
    assert isinstance(report.insights, tuple) and len(report.insights) > 0
    assert isinstance(report.actions, tuple) and len(report.actions) > 0


def test_scenario_10_order_preservation(
    report_builder: ReportBuilder,
    sample_rule_quality: RecommendationRule,
    sample_rule_delivery: RecommendationRule
):
    """
    Scenario 10: ReportBuilder strictly preserves candidate rule ordering from SelectionResult.
    """
    item_quality = SelectedRecommendation(aspect="QUALITY", risk_level="HIGH", rule=sample_rule_quality, priority="IMMEDIATE")
    item_delivery = SelectedRecommendation(aspect="DELIVERY", risk_level="MEDIUM", rule=sample_rule_delivery, priority="HIGH")

    selection_result = SelectionResult(
        selected=(item_quality, item_delivery),
        highest_priority="IMMEDIATE",
        recommendation_count=2
    )

    report = report_builder.build(selection_result)

    # Actions list should contain quality actions before delivery actions
    actions_text = " ".join(report.actions)
    quality_act_idx = actions_text.find("Inspect product stock")
    delivery_act_idx = actions_text.find("Dispatch orders quickly")

    assert quality_act_idx != -1
    assert delivery_act_idx != -1
    assert quality_act_idx < delivery_act_idx

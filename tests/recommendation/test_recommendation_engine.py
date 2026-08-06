"""
Unit & Integration Tests for Phase 8 – Recommendation Engine Integration.
Verifies end-to-end recommendation pipeline execution, constructor dependency injection, timing, metadata, and exception handling.
"""

import pytest
from unittest.mock import MagicMock, call

from core.business_risk.models.business_risk_result import BusinessRiskResult
from core.business_risk.models.aspect_risk import AspectRisk
from core.business_risk.models.risk_level import RiskLevel

from core.recommendation.constants.versions import RECOMMENDATION_VERSION
from core.recommendation.engine.recommendation_engine import RecommendationEngine
from core.recommendation.dto.recommendation_result import RecommendationResult, RecommendationMetadata
from core.recommendation.dto.recommendation_context import RecommendationContext
from core.recommendation.selector.models import SelectionResult
from core.recommendation.report.models import RecommendationReport
from core.recommendation.interpreter.risk_interpreter import RiskInterpreter
from core.recommendation.selector import ActionSelector
from core.recommendation.report import ReportBuilder
from core.recommendation.formatter import ResponseFormatter
from core.recommendation.exceptions import (
    RecommendationError,
    RecommendationGenerationError,
)
from core.recommendation.selector.exceptions import SelectionValidationError


@pytest.fixture
def recommendation_engine() -> RecommendationEngine:
    return RecommendationEngine()


@pytest.fixture
def high_risk_result() -> BusinessRiskResult:
    return BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=85.0, level="HIGH"),
        delivery=AspectRisk(aspect="delivery", score=20.0, level="LOW"),
        trust=AspectRisk(aspect="trust", score=60.0, level="MEDIUM"),
        business_risk_index=75.0,
        business_risk_level=RiskLevel.HIGH,
    )


@pytest.fixture
def healthy_risk_result() -> BusinessRiskResult:
    return BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=10.0, level="LOW"),
        delivery=AspectRisk(aspect="delivery", score=12.0, level="LOW"),
        trust=AspectRisk(aspect="trust", score=15.0, level="LOW"),
        business_risk_index=12.0,
        business_risk_level=RiskLevel.LOW,
    )


@pytest.fixture
def medium_risk_result() -> BusinessRiskResult:
    return BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=20.0, level="LOW"),
        delivery=AspectRisk(aspect="delivery", score=55.0, level="MEDIUM"),
        trust=AspectRisk(aspect="trust", score=18.0, level="LOW"),
        business_risk_index=40.0,
        business_risk_level=RiskLevel.MEDIUM,
    )


def test_scenario_1_high_risk_business_produces_recommendation_result(
    recommendation_engine: RecommendationEngine, high_risk_result: BusinessRiskResult
):
    """Scenario 1: Valid high-risk business produces complete RecommendationResult."""
    result = recommendation_engine.generate_recommendation(high_risk_result)

    assert isinstance(result, RecommendationResult)
    assert result.report is not None
    assert "QUALITY" in result.report.summary.upper() or "HIGH" in result.report.summary.upper()
    assert result.metadata.highest_priority in ["IMMEDIATE", "HIGH"]
    assert result.version == RECOMMENDATION_VERSION


def test_scenario_2_healthy_business_produces_maintenance_recommendation(
    recommendation_engine: RecommendationEngine, healthy_risk_result: BusinessRiskResult
):
    """Scenario 2: Healthy business produces maintenance recommendation report."""
    result = recommendation_engine.generate_recommendation(healthy_risk_result)

    assert isinstance(result, RecommendationResult)
    assert result.report is not None
    assert len(result.report.actions) > 0
    assert result.metadata.highest_priority in ["NORMAL", "LOW"]


def test_scenario_3_medium_risk_business_produces_expected_recommendation(
    recommendation_engine: RecommendationEngine, medium_risk_result: BusinessRiskResult
):
    """Scenario 3: Medium-risk business produces expected recommendation report."""
    result = recommendation_engine.generate_recommendation(medium_risk_result)

    assert isinstance(result, RecommendationResult)
    assert result.report is not None
    assert len(result.report.actions) > 0


def test_scenario_4_none_or_invalid_input_raises_recommendation_generation_error(
    recommendation_engine: RecommendationEngine,
):
    """Scenario 4: None or non-BusinessRiskResult input raises RecommendationGenerationError."""
    with pytest.raises(RecommendationGenerationError) as exc_info:
        recommendation_engine.generate_recommendation(None)
    assert "BusinessRiskResult" in str(exc_info.value)

    with pytest.raises(RecommendationGenerationError) as exc_info:
        recommendation_engine.generate_recommendation("invalid_string_input")  # type: ignore
    assert "BusinessRiskResult" in str(exc_info.value)


def test_scenario_5_unexpected_dependency_exception_wrapped(high_risk_result: BusinessRiskResult):
    """Scenario 5: Unexpected exception inside dependency is wrapped into RecommendationGenerationError."""
    mock_interpreter = MagicMock()
    mock_interpreter.interpret.side_effect = RuntimeError("Unexpected internal crash")

    engine = RecommendationEngine(interpreter=mock_interpreter)

    with pytest.raises(RecommendationGenerationError) as exc_info:
        engine.generate_recommendation(high_risk_result)

    assert "Recommendation generation failed" in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, RuntimeError)


def test_scenario_6_constructor_injection(high_risk_result: BusinessRiskResult):
    """Scenario 6: Constructor injection uses provided mock components."""
    mock_interpreter = MagicMock(spec=RiskInterpreter)
    mock_selector = MagicMock(spec=ActionSelector)
    mock_report_builder = MagicMock(spec=ReportBuilder)
    mock_formatter = MagicMock(spec=ResponseFormatter)

    dummy_context = MagicMock(spec=RecommendationContext)
    dummy_selection = MagicMock(spec=SelectionResult)
    dummy_report = MagicMock(spec=RecommendationReport)
    dummy_result = MagicMock(spec=RecommendationResult)

    mock_interpreter.interpret.return_value = dummy_context
    mock_selector.select.return_value = dummy_selection
    mock_report_builder.build.return_value = dummy_report
    mock_formatter.format.return_value = dummy_result

    engine = RecommendationEngine(
        interpreter=mock_interpreter,
        selector=mock_selector,
        report_builder=mock_report_builder,
        formatter=mock_formatter,
    )

    result = engine.generate_recommendation(high_risk_result)

    assert result == dummy_result
    mock_interpreter.interpret.assert_called_once_with(high_risk_result)
    mock_selector.select.assert_called_once_with(dummy_context)
    mock_report_builder.build.assert_called_once_with(dummy_selection)
    assert mock_formatter.format.call_count == 1


def test_scenario_7_pipeline_execution_order_and_data_flow(high_risk_result: BusinessRiskResult):
    """Scenario 7: Pipeline components called strictly in order with exact output of previous step."""
    call_order = []

    mock_interpreter = MagicMock(spec=RiskInterpreter)
    mock_selector = MagicMock(spec=ActionSelector)
    mock_report_builder = MagicMock(spec=ReportBuilder)
    mock_formatter = MagicMock(spec=ResponseFormatter)

    out_context = MagicMock(name="RecommendationContext")
    out_selection = MagicMock(name="SelectionResult")
    out_report = MagicMock(name="RecommendationReport")
    out_result = MagicMock(name="RecommendationResult")

    def interpret_side_effect(risk_res):
        call_order.append("interpreter")
        return out_context

    def select_side_effect(ctx):
        call_order.append("selector")
        assert ctx == out_context
        return out_selection

    def build_side_effect(sel):
        call_order.append("report_builder")
        assert sel == out_selection
        return out_report

    def format_side_effect(rep, st):
        call_order.append("formatter")
        assert rep == out_report
        return out_result

    mock_interpreter.interpret.side_effect = interpret_side_effect
    mock_selector.select.side_effect = select_side_effect
    mock_report_builder.build.side_effect = build_side_effect
    mock_formatter.format.side_effect = format_side_effect

    engine = RecommendationEngine(
        interpreter=mock_interpreter,
        selector=mock_selector,
        report_builder=mock_report_builder,
        formatter=mock_formatter,
    )

    res = engine.generate_recommendation(high_risk_result)

    assert res == out_result
    assert call_order == ["interpreter", "selector", "report_builder", "formatter"]


def test_scenario_8_processing_time_non_negative(
    recommendation_engine: RecommendationEngine, high_risk_result: BusinessRiskResult
):
    """Scenario 8: RecommendationResult processing_time_ms is >= 0 integer."""
    result = recommendation_engine.generate_recommendation(high_risk_result)

    assert isinstance(result.processing_time_ms, int)
    assert result.processing_time_ms >= 0


def test_scenario_9_metadata_populated(
    recommendation_engine: RecommendationEngine, high_risk_result: BusinessRiskResult
):
    """Scenario 9: highest_priority, recommendation_count, and generated_at metadata fields are populated."""
    result = recommendation_engine.generate_recommendation(high_risk_result)

    assert isinstance(result.metadata, RecommendationMetadata)
    assert result.metadata.highest_priority != ""
    assert result.metadata.recommendation_count > 0
    assert result.metadata.generated_at != ""


def test_scenario_10_full_integration(
    recommendation_engine: RecommendationEngine, high_risk_result: BusinessRiskResult
):
    """Scenario 10: Full integration verifies BusinessRiskResult -> RecommendationResult complete content."""
    result = recommendation_engine.generate_recommendation(high_risk_result)

    assert isinstance(result, RecommendationResult)

    # Report assertions
    assert hasattr(result.report, "summary") and isinstance(result.report.summary, str) and len(result.report.summary) > 0
    assert hasattr(result.report, "insights") and isinstance(result.report.insights, (list, tuple)) and len(result.report.insights) > 0
    assert hasattr(result.report, "actions") and isinstance(result.report.actions, (list, tuple)) and len(result.report.actions) > 0

    # Metadata assertions
    assert hasattr(result.metadata, "highest_priority") and result.metadata.highest_priority != ""
    assert hasattr(result.metadata, "recommendation_count") and result.metadata.recommendation_count > 0
    assert hasattr(result.metadata, "generated_at") and result.metadata.generated_at != ""

    # Version assertion
    assert result.version == RECOMMENDATION_VERSION


def test_scenario_11_domain_exceptions_propagated_unchanged(high_risk_result: BusinessRiskResult):
    """Scenario 11: RecommendationError domain exceptions are re-raised without being wrapped."""
    mock_selector = MagicMock()
    mock_selector.select.side_effect = SelectionValidationError("Validation failed on selection")

    engine = RecommendationEngine(selector=mock_selector)

    with pytest.raises(SelectionValidationError) as exc_info:
        engine.generate_recommendation(high_risk_result)

    assert "Validation failed on selection" in str(exc_info.value)
    assert not isinstance(exc_info.value, RecommendationGenerationError)

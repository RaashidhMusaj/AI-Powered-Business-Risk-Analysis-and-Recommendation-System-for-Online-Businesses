"""
Unit Tests for Phase 7 – Response Formatter Component.
Verifies validation, timing calculations, DTO mapping, metadata enrichment, immutability, and pure transformation.
"""

import time
import pytest
from datetime import datetime, timezone
from dataclasses import FrozenInstanceError

from core.recommendation.constants.versions import RECOMMENDATION_VERSION
from core.recommendation.report.models import RecommendationReport
from core.recommendation.dto.recommendation_result import RecommendationResult, RecommendationMetadata
from core.recommendation.formatter.formatter import ResponseFormatter
from core.recommendation.formatter.validator import ResponseValidator
from core.recommendation.formatter.mapper import ResponseMapper
from core.recommendation.formatter.exceptions import (
    ResponseFormattingError,
    ResponseValidationError,
)


@pytest.fixture
def response_formatter() -> ResponseFormatter:
    return ResponseFormatter()


@pytest.fixture
def valid_report() -> RecommendationReport:
    return RecommendationReport(
        summary="High priority risks identified in Quality aspect.",
        insights=(
            "Major defect rate increased by 15%.",
            "Customer satisfaction dropped below threshold.",
        ),
        actions=(
            "Inspect product stock immediately.",
            "Halt defective batches.",
        ),
        highest_priority="IMMEDIATE",
        recommendation_count=2,
        generated_at=datetime(2026, 8, 1, 12, 30, 45, tzinfo=timezone.utc),
    )


def test_scenario_1_valid_report_produces_recommendation_result(
    response_formatter: ResponseFormatter, valid_report: RecommendationReport
):
    """Scenario 1: Valid report produces a complete RecommendationResult."""
    start_time = time.perf_counter()
    result = response_formatter.format(valid_report, start_time)

    assert isinstance(result, RecommendationResult)
    assert result.report == valid_report
    assert isinstance(result.metadata, RecommendationMetadata)
    assert result.version == RECOMMENDATION_VERSION


def test_scenario_2_processing_time_integer_ms(
    response_formatter: ResponseFormatter, valid_report: RecommendationReport
):
    """Scenario 2: Processing time is calculated as integer milliseconds >= 0."""
    start_time = time.perf_counter()
    time.sleep(0.005)  # Sleep 5ms
    result = response_formatter.format(valid_report, start_time)

    assert isinstance(result.processing_time_ms, int)
    assert result.processing_time_ms >= 0


def test_scenario_3_metadata_copied_correctly(
    response_formatter: ResponseFormatter, valid_report: RecommendationReport
):
    """Scenario 3: RecommendationMetadata fields are populated correctly from report."""
    start_time = time.perf_counter()
    result = response_formatter.format(valid_report, start_time)

    assert result.metadata.highest_priority == "IMMEDIATE"
    assert result.metadata.recommendation_count == 2
    assert result.metadata.generated_at == "2026-08-01T12:30:45+00:00"


def test_scenario_4_generated_timestamp_preserved(
    response_formatter: ResponseFormatter, valid_report: RecommendationReport
):
    """Scenario 4: RecommendationResult preserves report.generated_at without regeneration."""
    start_time = time.perf_counter()
    result = response_formatter.format(valid_report, start_time)

    assert result.generated_timestamp == valid_report.generated_at
    assert result.generated_timestamp == datetime(2026, 8, 1, 12, 30, 45, tzinfo=timezone.utc)


def test_scenario_5_empty_report_raises_validation_error(
    response_formatter: ResponseFormatter,
):
    """Scenario 5: Empty report (empty summary, insights, or actions) raises ResponseValidationError."""
    empty_summary_report = RecommendationReport(
        summary="",
        insights=("Insight 1",),
        actions=("Action 1",),
        highest_priority="MEDIUM",
        recommendation_count=1,
        generated_at=datetime.now(timezone.utc),
    )
    empty_insights_report = RecommendationReport(
        summary="Summary text",
        insights=(),
        actions=("Action 1",),
        highest_priority="MEDIUM",
        recommendation_count=1,
        generated_at=datetime.now(timezone.utc),
    )
    empty_actions_report = RecommendationReport(
        summary="Summary text",
        insights=("Insight 1",),
        actions=(),
        highest_priority="MEDIUM",
        recommendation_count=1,
        generated_at=datetime.now(timezone.utc),
    )

    start_time = time.perf_counter()
    with pytest.raises(ResponseValidationError):
        response_formatter.format(empty_summary_report, start_time)

    with pytest.raises(ResponseValidationError):
        response_formatter.format(empty_insights_report, start_time)

    with pytest.raises(ResponseValidationError):
        response_formatter.format(empty_actions_report, start_time)


def test_scenario_6_immutable_recommendation_result_raises_frozen_instance_error(
    response_formatter: ResponseFormatter, valid_report: RecommendationReport
):
    """Scenario 6: Modifying RecommendationResult attributes raises FrozenInstanceError."""
    start_time = time.perf_counter()
    result = response_formatter.format(valid_report, start_time)

    with pytest.raises(FrozenInstanceError):
        result.version = "v2"

    with pytest.raises(FrozenInstanceError):
        result.processing_time_ms = 100

    with pytest.raises(FrozenInstanceError):
        result.metadata.highest_priority = "LOW"


def test_scenario_7_version_propagated(
    response_formatter: ResponseFormatter, valid_report: RecommendationReport
):
    """Scenario 7: Version is propagated correctly from RECOMMENDATION_VERSION (default v1)."""
    start_time = time.perf_counter()
    result = response_formatter.format(valid_report, start_time)

    assert result.version == "v1"
    assert result.version == RECOMMENDATION_VERSION


def test_scenario_8_iso_timestamp_formatting(
    response_formatter: ResponseFormatter, valid_report: RecommendationReport
):
    """Scenario 8: ISO timestamp formatting matches ISO 8601 standard format."""
    start_time = time.perf_counter()
    result = response_formatter.format(valid_report, start_time)

    expected_iso = "2026-08-01T12:30:45+00:00"
    assert result.metadata.generated_at == expected_iso


def test_scenario_9_summary_insights_actions_unchanged(
    response_formatter: ResponseFormatter, valid_report: RecommendationReport
):
    """Scenario 9: Summary, insights, and actions remain unchanged after formatting."""
    start_time = time.perf_counter()
    result = response_formatter.format(valid_report, start_time)

    assert result.report.summary == valid_report.summary
    assert result.report.insights == valid_report.insights
    assert result.report.actions == valid_report.actions


def test_scenario_10_null_or_invalid_generated_at_raises_validation_error(
    response_formatter: ResponseFormatter,
):
    """Scenario 10: Null report or report with missing/invalid generated_at raises ResponseValidationError."""
    start_time = time.perf_counter()

    with pytest.raises(ResponseValidationError):
        response_formatter.format(None, start_time)

    class InvalidReportNoDate:
        summary = "Summary"
        insights = ("Insight",)
        actions = ("Action",)
        generated_at = None

    with pytest.raises(ResponseValidationError):
        response_formatter.format(InvalidReportNoDate(), start_time)


def test_scenario_11_pure_transformation_unmutated_input(
    response_formatter: ResponseFormatter, valid_report: RecommendationReport
):
    """Scenario 11: Formatting is a pure transformation; input report values and object IDs remain unchanged."""
    summary_id_before = id(valid_report.summary)
    insights_id_before = id(valid_report.insights)
    actions_id_before = id(valid_report.actions)
    generated_at_before = valid_report.generated_at

    start_time = time.perf_counter()
    result = response_formatter.format(valid_report, start_time)

    # Values check
    assert result.report.summary == valid_report.summary
    assert result.report.insights == valid_report.insights
    assert result.report.actions == valid_report.actions
    assert valid_report.generated_at == generated_at_before

    # Object identity check
    assert id(valid_report.summary) == summary_id_before
    assert id(valid_report.insights) == insights_id_before
    assert id(valid_report.actions) == actions_id_before

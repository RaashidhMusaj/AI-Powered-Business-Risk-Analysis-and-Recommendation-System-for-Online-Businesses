"""
End-to-End Pipeline Integration Tests for Phase 9 – Business Risk Pipeline Integration.
Verifies dependency graph, RecommendationService integration, unified AnalysisResult DTO, error handling, and API mapping.
"""

import pytest
from unittest.mock import MagicMock

from core.business_risk.models.business_risk_result import BusinessRiskResult
from core.business_risk.models.aspect_risk import AspectRisk
from core.business_risk.models.risk_level import RiskLevel

from core.models.analysis_result import AnalysisResult
from core.recommendation.service.recommendation_service import RecommendationService
from core.recommendation.engine.recommendation_engine import RecommendationEngine
from core.recommendation.dto.recommendation_result import RecommendationResult, RecommendationMetadata
from core.recommendation.constants.versions import RECOMMENDATION_VERSION
from core.recommendation.exceptions import RecommendationGenerationError

from app.adapters.ai_engine_adapter import AIEngineAdapter
from app.mappers.analysis_mapper import AnalysisMapper
from app.api.dependencies.services import get_recommendation_service


@pytest.fixture
def recommendation_service() -> RecommendationService:
    return RecommendationService()


@pytest.fixture
def ai_adapter(recommendation_service: RecommendationService) -> AIEngineAdapter:
    return AIEngineAdapter(recommendation_service=recommendation_service)


@pytest.fixture
def high_risk_result() -> BusinessRiskResult:
    return BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=82.0, level="HIGH"),
        delivery=AspectRisk(aspect="delivery", score=25.0, level="LOW"),
        trust=AspectRisk(aspect="trust", score=65.0, level="MEDIUM"),
        business_risk_index=76.0,
        business_risk_level=RiskLevel.HIGH,
    )


@pytest.fixture
def healthy_risk_result() -> BusinessRiskResult:
    return BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=12.0, level="LOW"),
        delivery=AspectRisk(aspect="delivery", score=10.0, level="LOW"),
        trust=AspectRisk(aspect="trust", score=14.0, level="LOW"),
        business_risk_index=12.0,
        business_risk_level=RiskLevel.LOW,
    )


@pytest.fixture
def medium_risk_result() -> BusinessRiskResult:
    return BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=20.0, level="LOW"),
        delivery=AspectRisk(aspect="delivery", score=58.0, level="MEDIUM"),
        trust=AspectRisk(aspect="trust", score=18.0, level="LOW"),
        business_risk_index=42.0,
        business_risk_level=RiskLevel.MEDIUM,
    )


def test_dependency_graph_verification():
    """Dependency Graph Verification: Verify chain of dependencies from app to core engines."""
    service_dep = get_recommendation_service()
    assert isinstance(service_dep, RecommendationService)
    assert isinstance(service_dep.engine, RecommendationEngine)

    adapter = AIEngineAdapter(recommendation_service=service_dep)
    assert adapter._recommendation_service == service_dep
    assert adapter._recommendation_service.engine == service_dep.engine


def test_scenario_1_high_risk_business_integration(
    recommendation_service: RecommendationService, high_risk_result: BusinessRiskResult
):
    """Scenario 1: High-risk business produces valid RecommendationResult via RecommendationService."""
    rec_result = recommendation_service.generate_recommendation(high_risk_result)

    assert isinstance(rec_result, RecommendationResult)
    assert "QUALITY" in rec_result.report.summary.upper() or "HIGH" in rec_result.report.summary.upper()
    assert rec_result.metadata.highest_priority in ["IMMEDIATE", "HIGH"]


def test_scenario_2_healthy_business_integration(
    recommendation_service: RecommendationService, healthy_risk_result: BusinessRiskResult
):
    """Scenario 2: Healthy business produces maintenance recommendation summary and actions."""
    rec_result = recommendation_service.generate_recommendation(healthy_risk_result)

    assert isinstance(rec_result, RecommendationResult)
    assert len(rec_result.report.actions) > 0
    assert rec_result.metadata.highest_priority in ["NORMAL", "LOW"]


def test_scenario_3_medium_risk_business_integration(
    recommendation_service: RecommendationService, medium_risk_result: BusinessRiskResult
):
    """Scenario 3: Medium risk business produces warning recommendations."""
    rec_result = recommendation_service.generate_recommendation(medium_risk_result)

    assert isinstance(rec_result, RecommendationResult)
    assert len(rec_result.report.actions) > 0


def test_scenario_4_recommendation_service_failure_propagation(high_risk_result: BusinessRiskResult):
    """Scenario 4: Recommendation service / engine failure returns proper exception."""
    mock_engine = MagicMock()
    mock_engine.generate_recommendation.side_effect = RecommendationGenerationError("Simulated engine crash")

    service = RecommendationService(engine=mock_engine)

    with pytest.raises(RecommendationGenerationError) as exc_info:
        service.generate_recommendation(high_risk_result)

    assert "Simulated engine crash" in str(exc_info.value)


def test_scenario_5_invalid_request_validation_error(recommendation_service: RecommendationService):
    """Scenario 5: Invalid request (None or non-BusinessRiskResult) produces validation error."""
    with pytest.raises(RecommendationGenerationError):
        recommendation_service.generate_recommendation(None)

    with pytest.raises(RecommendationGenerationError):
        recommendation_service.generate_recommendation("invalid_type")  # type: ignore


def test_scenario_6_unified_analysis_result_structure(
    recommendation_service: RecommendationService, high_risk_result: BusinessRiskResult
):
    """Scenario 6: AnalysisResult DTO encapsulates BusinessRiskResult and RecommendationResult."""
    rec_result = recommendation_service.generate_recommendation(high_risk_result)
    unified = AnalysisResult(business_risk=high_risk_result, recommendation=rec_result)

    assert isinstance(unified, AnalysisResult)
    assert unified.business_risk == high_risk_result
    assert unified.recommendation == rec_result


def test_scenario_7_metadata_fields_verification(
    recommendation_service: RecommendationService, high_risk_result: BusinessRiskResult
):
    """Scenario 7: Metadata fields (highestPriority, recommendationCount, generatedAt, processingTimeMs, version)."""
    rec_result = recommendation_service.generate_recommendation(high_risk_result)

    assert isinstance(rec_result.metadata, RecommendationMetadata)
    assert rec_result.metadata.highest_priority != ""
    assert rec_result.metadata.recommendation_count > 0
    assert rec_result.metadata.generated_at != ""
    assert isinstance(rec_result.processing_time_ms, int)
    assert rec_result.processing_time_ms >= 0
    assert rec_result.version == RECOMMENDATION_VERSION


def test_scenario_8_end_to_end_mapper_and_api_payload_verification(
    recommendation_service: RecommendationService, high_risk_result: BusinessRiskResult
):
    """Scenario 8: Complete end-to-end verification via AnalysisMapper producing API-ready dictionary."""
    rec_result = recommendation_service.generate_recommendation(high_risk_result)

    mock_pipeline_output = {
        "product": {
            "title": "Test Product",
            "url": "https://daraz.com.np/products/test-item",
            "total_reviews": 10,
            "overall_rating": 4.5,
            "seller_name": "Test Seller",
        },
        "business": high_risk_result,
        "quality": high_risk_result.quality,
        "delivery": high_risk_result.delivery,
        "trust": high_risk_result.trust,
        "recommendation": rec_result,
    }

    mapped = AnalysisMapper.to_api_result(mock_pipeline_output)

    assert "product" in mapped
    assert "risks" in mapped
    assert "recommendation" in mapped

    rec_payload = mapped["recommendation"]
    assert rec_payload is not None
    assert "report" in rec_payload
    assert "metadata" in rec_payload
    assert "summary" in rec_payload["report"]
    assert "insights" in rec_payload["report"]
    assert "actions" in rec_payload["report"]
    assert rec_payload["metadata"]["highestPriority"] in ["IMMEDIATE", "HIGH"]
    assert rec_payload["metadata"]["recommendationCount"] > 0
    assert rec_payload["version"] == RECOMMENDATION_VERSION
    assert isinstance(rec_payload["processingTimeMs"], int)

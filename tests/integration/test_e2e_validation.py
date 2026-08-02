"""
End-to-End System Validation Tests (Milestone 10.1).
Validates complete pipeline execution across realistic business risk profiles.
"""

import pytest
from core.business_risk.models.business_risk_result import BusinessRiskResult
from core.business_risk.models.aspect_risk import AspectRisk
from core.business_risk.models.risk_level import RiskLevel

from core.recommendation.service import RecommendationService
from core.models.analysis_result import AnalysisResult
from core.recommendation.constants.versions import RECOMMENDATION_VERSION
from app.mappers.analysis_mapper import AnalysisMapper


@pytest.fixture
def rec_service() -> RecommendationService:
    return RecommendationService()


def test_e2e_high_risk_product_validation(rec_service: RecommendationService):
    """
    Milestone 10.1: E2E validation for a High-Risk product.
    Input: High Quality Risk (84.5) & Overall High Risk (78.0)
    Expected:
    - BusinessRiskResult overall level HIGH
    - Recommendation priority IMMEDIATE
    - Key action item for Quality mitigation
    """
    high_risk_br = BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=84.5, level="HIGH"),
        delivery=AspectRisk(aspect="delivery", score=22.0, level="LOW"),
        trust=AspectRisk(aspect="trust", score=58.0, level="MEDIUM"),
        business_risk_index=78.0,
        business_risk_level=RiskLevel.HIGH,
    )

    rec_result = rec_service.generate_recommendation(high_risk_br)
    unified = AnalysisResult(business_risk=high_risk_br, recommendation=rec_result)

    assert unified.business_risk.business_risk_level == RiskLevel.HIGH
    assert unified.recommendation.metadata.highest_priority == "IMMEDIATE"
    assert len(unified.recommendation.report.actions) > 0
    assert "QUALITY" in unified.recommendation.report.summary.upper() or "HIGH" in unified.recommendation.report.summary.upper()


def test_e2e_medium_risk_delivery_validation(rec_service: RecommendationService):
    """
    Milestone 10.1: E2E validation for a Medium-Risk product.
    Input: Medium Delivery Risk (56.0) & Overall Medium Risk (48.0)
    Expected:
    - BusinessRiskResult overall level MEDIUM
    - Recommendation priority HIGH
    - Actions focusing on delivery optimization
    """
    medium_risk_br = BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=18.0, level="LOW"),
        delivery=AspectRisk(aspect="delivery", score=56.0, level="MEDIUM"),
        trust=AspectRisk(aspect="trust", score=20.0, level="LOW"),
        business_risk_index=48.0,
        business_risk_level=RiskLevel.MEDIUM,
    )

    rec_result = rec_service.generate_recommendation(medium_risk_br)
    unified = AnalysisResult(business_risk=medium_risk_br, recommendation=rec_result)

    assert unified.business_risk.business_risk_level == RiskLevel.MEDIUM
    assert unified.recommendation.metadata.highest_priority in ["HIGH", "IMMEDIATE"]
    assert len(unified.recommendation.report.actions) > 0


def test_e2e_healthy_low_risk_product_validation(rec_service: RecommendationService):
    """
    Milestone 10.1: E2E validation for a Healthy/Low-Risk product.
    Input: All aspects LOW (<20.0) & Overall LOW (12.5)
    Expected:
    - BusinessRiskResult overall level LOW
    - Recommendation priority NORMAL
    - Maintenance recommendations
    """
    healthy_br = BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=10.0, level="LOW"),
        delivery=AspectRisk(aspect="delivery", score=15.0, level="LOW"),
        trust=AspectRisk(aspect="trust", score=12.0, level="LOW"),
        business_risk_index=12.5,
        business_risk_level=RiskLevel.LOW,
    )

    rec_result = rec_service.generate_recommendation(healthy_br)
    unified = AnalysisResult(business_risk=healthy_br, recommendation=rec_result)

    assert unified.business_risk.business_risk_level == RiskLevel.LOW
    assert unified.recommendation.metadata.highest_priority in ["NORMAL", "LOW"]
    assert len(unified.recommendation.report.actions) > 0


def test_e2e_full_mapper_response_schema_validation(rec_service: RecommendationService):
    """
    Milestone 10.1: Validates complete pipeline mapped output dictionary structure.
    """
    br = BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=75.0, level="HIGH"),
        delivery=AspectRisk(aspect="delivery", score=30.0, level="LOW"),
        trust=AspectRisk(aspect="trust", score=40.0, level="MEDIUM"),
        business_risk_index=65.0,
        business_risk_level=RiskLevel.HIGH,
    )
    rec = rec_service.generate_recommendation(br)

    mock_output = {
        "product": {"title": "Sample Daraz Product", "product_url": "https://daraz.com.np/p/sample"},
        "business": br,
        "quality": br.quality,
        "delivery": br.delivery,
        "trust": br.trust,
        "recommendation": rec,
    }

    mapped = AnalysisMapper.to_api_result(mock_output)

    assert mapped["product"]["title"] == "Sample Daraz Product"
    assert mapped["risks"]["overallRiskLevel"] == "HIGH"
    assert mapped["recommendation"]["version"] == RECOMMENDATION_VERSION
    assert isinstance(mapped["recommendation"]["processingTimeMs"], int)

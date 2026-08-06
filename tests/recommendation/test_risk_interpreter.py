"""
Unit Tests for Phase 2 – Risk Interpreter Component.
Verifies risk extraction, ranking abstraction, tie-breaking, and context generation.
"""

import pytest
from core.business_risk.models.business_risk_result import BusinessRiskResult
from core.business_risk.models.aspect_risk import AspectRisk
from core.business_risk.models.risk_level import RiskLevel
from core.recommendation.interpreter.risk_interpreter import RiskInterpreter


@pytest.fixture
def interpreter() -> RiskInterpreter:
    return RiskInterpreter()


def test_scenario_1_high_risk_product(interpreter: RiskInterpreter):
    """
    Scenario 1:
    Overall: HIGH
    Quality: HIGH (81.2)
    Trust: MEDIUM (56.8)
    Delivery: LOW (22.3)
    
    Expected:
    Priority: IMMEDIATE
    Main Issue: QUALITY
    Secondary Issue: TRUST
    Good Area: DELIVERY
    """
    risk_result = BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=81.2, level="HIGH"),
        delivery=AspectRisk(aspect="delivery", score=22.3, level="LOW"),
        trust=AspectRisk(aspect="trust", score=56.8, level="MEDIUM"),
        business_risk_index=78.4,
        business_risk_level=RiskLevel.HIGH
    )

    context = interpreter.interpret(risk_result)

    assert context.priority == "IMMEDIATE"
    assert context.main_issue == "QUALITY"
    assert context.secondary_issue == "TRUST"
    assert context.good_area == "DELIVERY"
    assert context.interpreted_risks["businessStatus"] == "CRITICAL"
    assert context.interpreted_risks["primaryFocus"] == "QUALITY"
    assert context.risk_summary["highRiskCount"] == 1
    assert context.risk_summary["mediumRiskCount"] == 1
    assert context.risk_summary["lowRiskCount"] == 1


def test_scenario_2_healthy_product_all_low(interpreter: RiskInterpreter):
    """
    Scenario 2:
    Overall: LOW
    Quality: LOW (15.0)
    Delivery: LOW (10.0)
    Trust: LOW (12.0)

    Expected:
    Priority: NORMAL
    Business Status: HEALTHY
    Main Issue: None (No Significant Issue)
    Secondary Issue: None
    Good Area: DELIVERY (lowest score)
    """
    risk_result = BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=15.0, level="LOW"),
        delivery=AspectRisk(aspect="delivery", score=10.0, level="LOW"),
        trust=AspectRisk(aspect="trust", score=12.0, level="LOW"),
        business_risk_index=12.3,
        business_risk_level=RiskLevel.LOW
    )

    context = interpreter.interpret(risk_result)

    assert context.priority == "NORMAL"
    assert context.interpreted_risks["businessStatus"] == "HEALTHY"
    assert context.main_issue is None
    assert context.secondary_issue is None
    assert context.good_area == "DELIVERY"
    assert context.risk_summary["lowRiskCount"] == 3
    assert context.risk_summary["highRiskCount"] == 0
    assert context.risk_summary["highestRiskLevel"] == "LOW"
    assert context.risk_summary["lowestRiskLevel"] == "LOW"


def test_scenario_3_medium_risk_delivery_spike(interpreter: RiskInterpreter):
    """
    Scenario 3:
    Overall: MEDIUM
    Quality: MEDIUM (45.0)
    Delivery: HIGH (75.0)
    Trust: LOW (20.0)

    Expected:
    Main Issue: DELIVERY
    Good Area: TRUST
    Priority: HIGH
    Business Status: WARNING
    """
    risk_result = BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=45.0, level="MEDIUM"),
        delivery=AspectRisk(aspect="delivery", score=75.0, level="HIGH"),
        trust=AspectRisk(aspect="trust", score=20.0, level="LOW"),
        business_risk_index=46.7,
        business_risk_level=RiskLevel.MEDIUM
    )

    context = interpreter.interpret(risk_result)

    assert context.priority == "HIGH"
    assert context.main_issue == "DELIVERY"
    assert context.secondary_issue == "QUALITY"
    assert context.good_area == "TRUST"
    assert context.interpreted_risks["businessStatus"] == "WARNING"


def test_scenario_4_crisp_score_tie_breaking(interpreter: RiskInterpreter):
    """
    Scenario 4: Tie Breaking by Crisp Score when risk levels are identical.
    Quality: HIGH (90.0)
    Delivery: HIGH (70.0)
    Trust: HIGH (60.0)

    Expected:
    Main Issue: QUALITY (score 90 > 70)
    Secondary Issue: DELIVERY (score 70 > 60)
    Good Area: TRUST (score 60 lowest among HIGHs)
    """
    risk_result = BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=90.0, level="HIGH"),
        delivery=AspectRisk(aspect="delivery", score=70.0, level="HIGH"),
        trust=AspectRisk(aspect="trust", score=60.0, level="HIGH"),
        business_risk_index=73.3,
        business_risk_level=RiskLevel.HIGH
    )

    context = interpreter.interpret(risk_result)

    assert context.main_issue == "QUALITY"
    assert context.secondary_issue == "DELIVERY"
    assert context.good_area == "TRUST"
    assert context.risk_summary["highRiskCount"] == 3
    assert context.risk_summary["highestRiskLevel"] == "HIGH"
    assert context.risk_summary["lowestRiskLevel"] == "HIGH"

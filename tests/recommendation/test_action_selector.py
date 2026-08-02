"""
Unit Tests for Phase 5 – Action Selector Component.
Verifies rule selection, aspect querying, priority policy sorting, cross-aspect deduplication, and immutability.
"""

import pytest
from dataclasses import FrozenInstanceError
from unittest.mock import MagicMock

from core.business_risk.models.business_risk_result import BusinessRiskResult
from core.business_risk.models.aspect_risk import AspectRisk
from core.business_risk.models.risk_level import RiskLevel

from core.recommendation.dto.recommendation_context import RecommendationContext
from core.recommendation.knowledge.knowledge_base import RecommendationKnowledgeBase
from core.recommendation.knowledge.models import RecommendationRule

from core.recommendation.selector.selector import ActionSelector
from core.recommendation.selector.strategy import SelectionStrategy
from core.recommendation.selector.models import SelectionResult, SelectedRecommendation
from core.recommendation.selector.exceptions import (
    SelectionError,
    SelectionValidationError,
    SelectionFailedError,
)


@pytest.fixture
def knowledge_base() -> RecommendationKnowledgeBase:
    kb = RecommendationKnowledgeBase()
    kb.initialize()
    return kb


@pytest.fixture
def selector(knowledge_base: RecommendationKnowledgeBase) -> ActionSelector:
    return ActionSelector(knowledge_base=knowledge_base)


def test_scenario_1_high_risk_quality_product(selector: ActionSelector):
    """
    Scenario 1: High-risk quality product selects Quality and General rules in priority order.
    """
    risk_result = BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=81.2, level="HIGH"),
        delivery=AspectRisk(aspect="delivery", score=22.3, level="LOW"),
        trust=AspectRisk(aspect="trust", score=30.0, level="LOW"),
        business_risk_index=78.4,
        business_risk_level=RiskLevel.HIGH
    )
    context = RecommendationContext(
        business_risk_result=risk_result,
        priority="IMMEDIATE",
        main_issue="QUALITY",
        secondary_issue=None,
        good_area="DELIVERY",
        interpreted_risks={"businessStatus": "CRITICAL", "primaryFocus": "QUALITY"},
        risk_summary={"highestRiskLevel": "HIGH", "highRiskCount": 1, "mediumRiskCount": 0, "lowRiskCount": 2}
    )

    result = selector.select(context)

    assert isinstance(result, SelectionResult)
    assert result.recommendation_count >= 1
    selected_aspects = [item.aspect for item in result.selected]
    assert "QUALITY" in selected_aspects


def test_scenario_2_healthy_product_all_low(selector: ActionSelector):
    """
    Scenario 2: Healthy product (all low) selects maintenance/general rules only.
    """
    risk_result = BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=10.0, level="LOW"),
        delivery=AspectRisk(aspect="delivery", score=10.0, level="LOW"),
        trust=AspectRisk(aspect="trust", score=10.0, level="LOW"),
        business_risk_index=10.0,
        business_risk_level=RiskLevel.LOW
    )
    context = RecommendationContext(
        business_risk_result=risk_result,
        priority="NORMAL",
        main_issue=None,
        secondary_issue=None,
        good_area="QUALITY",
        interpreted_risks={"businessStatus": "HEALTHY", "primaryFocus": "GENERAL_MAINTENANCE"},
        risk_summary={"highestRiskLevel": "LOW", "highRiskCount": 0, "mediumRiskCount": 0, "lowRiskCount": 3}
    )

    result = selector.select(context)

    assert result.recommendation_count >= 1
    for item in result.selected:
        assert item.aspect == "GENERAL"


def test_scenario_3_multi_aspect_risk(selector: ActionSelector):
    """
    Scenario 3: Multi-aspect risk (Quality HIGH & Delivery HIGH) selects rules for both aspects.
    """
    risk_result = BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=85.0, level="HIGH"),
        delivery=AspectRisk(aspect="delivery", score=80.0, level="HIGH"),
        trust=AspectRisk(aspect="trust", score=20.0, level="LOW"),
        business_risk_index=82.0,
        business_risk_level=RiskLevel.HIGH
    )
    context = RecommendationContext(
        business_risk_result=risk_result,
        priority="IMMEDIATE",
        main_issue="QUALITY",
        secondary_issue="DELIVERY",
        good_area="TRUST",
        interpreted_risks={"businessStatus": "CRITICAL", "primaryFocus": "QUALITY"},
        risk_summary={"highestRiskLevel": "HIGH", "highRiskCount": 2, "mediumRiskCount": 0, "lowRiskCount": 1}
    )

    result = selector.select(context)

    selected_aspects = {item.aspect for item in result.selected}
    assert "QUALITY" in selected_aspects
    assert "DELIVERY" in selected_aspects


def test_scenario_4_no_matching_rules_raises_error():
    """
    Scenario 4: When knowledge base returns empty lists for queries, raises SelectionFailedError.
    """
    empty_kb = MagicMock(spec=RecommendationKnowledgeBase)
    empty_kb.get_rules.return_value = []
    empty_kb.get_general_rules.return_value = []

    mock_selector = ActionSelector(knowledge_base=empty_kb)

    context = RecommendationContext(
        business_risk_result=MagicMock(spec=BusinessRiskResult),
        priority="IMMEDIATE",
        main_issue="QUALITY"
    )

    with pytest.raises(SelectionFailedError) as exc_info:
        mock_selector.select(context)
    assert "No matching recommendation rules could be selected" in str(exc_info.value)


def test_scenario_5_priority_ordering(selector: ActionSelector):
    """
    Scenario 5: Priority ordering strictly follows IMMEDIATE -> HIGH -> NORMAL.
    """
    risk_result = BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=85.0, level="HIGH"),
        delivery=AspectRisk(aspect="delivery", score=80.0, level="HIGH"),
        trust=AspectRisk(aspect="trust", score=20.0, level="LOW"),
        business_risk_index=82.0,
        business_risk_level=RiskLevel.HIGH
    )
    context = RecommendationContext(
        business_risk_result=risk_result,
        priority="IMMEDIATE",
        main_issue="QUALITY",
        secondary_issue="DELIVERY",
        interpreted_risks={"businessStatus": "CRITICAL"}
    )

    result = selector.select(context)

    priorities = [item.priority for item in result.selected]
    weights = [{"IMMEDIATE": 3, "HIGH": 2, "NORMAL": 1}.get(p, 0) for p in priorities]
    # Check weights are sorted non-ascending (IMMEDIATE first)
    assert weights == sorted(weights, reverse=True)


def test_scenario_6_duplicate_rule_removal(selector: ActionSelector):
    """
    Scenario 6: Duplicate rule IDs are deduplicated.
    """
    risk_result = BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=85.0, level="HIGH"),
        delivery=AspectRisk(aspect="delivery", score=20.0, level="LOW"),
        trust=AspectRisk(aspect="trust", score=20.0, level="LOW"),
        business_risk_index=82.0,
        business_risk_level=RiskLevel.HIGH
    )
    context = RecommendationContext(
        business_risk_result=risk_result,
        priority="IMMEDIATE",
        main_issue="QUALITY"
    )

    result = selector.select(context)

    rule_ids = [item.rule.id for item in result.selected]
    assert len(rule_ids) == len(set(rule_ids))


def test_scenario_7_selection_result_immutability(selector: ActionSelector):
    """
    Scenario 7: SelectionResult and SelectedRecommendation are frozen and immutable.
    """
    risk_result = BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=10.0, level="LOW"),
        delivery=AspectRisk(aspect="delivery", score=10.0, level="LOW"),
        trust=AspectRisk(aspect="trust", score=10.0, level="LOW"),
        business_risk_index=10.0,
        business_risk_level=RiskLevel.LOW
    )
    context = RecommendationContext(
        business_risk_result=risk_result,
        priority="NORMAL",
        interpreted_risks={"businessStatus": "HEALTHY"}
    )

    result = selector.select(context)

    with pytest.raises(FrozenInstanceError):
        result.recommendation_count = 999  # type: ignore

    with pytest.raises(FrozenInstanceError):
        result.selected[0].aspect = "MODIFIED"  # type: ignore


def test_scenario_8_invalid_context_raises_validation_error(selector: ActionSelector):
    """
    Scenario 8: Null or invalid RecommendationContext raises SelectionValidationError.
    """
    with pytest.raises(SelectionValidationError):
        selector.select(None)  # type: ignore


def test_scenario_9_cross_aspect_rule_deduplication():
    """
    Scenario 9: Rules returned across both primary and secondary aspect queries are merged into SelectionResult exactly once.
    """
    shared_rule = RecommendationRule(
        id="shared_rule_001",
        aspect="QUALITY",
        risk_level="HIGH",
        title="Shared Rule",
        description="Desc",
        actions=("Action 1",),
        priority="HIGH"
    )

    mock_kb = MagicMock(spec=RecommendationKnowledgeBase)
    mock_kb.get_rules.return_value = [shared_rule]
    mock_kb.get_general_rules.return_value = []

    selector_instance = ActionSelector(knowledge_base=mock_kb)

    context = RecommendationContext(
        business_risk_result=MagicMock(spec=BusinessRiskResult),
        priority="HIGH",
        main_issue="QUALITY",
        secondary_issue="DELIVERY",
        interpreted_risks={"businessStatus": "WARNING"}
    )

    result = selector_instance.select(context)

    shared_count = sum(1 for item in result.selected if item.rule.id == "shared_rule_001")
    assert shared_count == 1

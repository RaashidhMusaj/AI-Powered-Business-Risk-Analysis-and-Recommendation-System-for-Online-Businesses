"""
Robustness & Error Recovery Tests (Milestone 10.4).
Verifies graceful handling of missing model files, corrupted rules, missing templates, and unexpected inputs.
"""

import pytest
from unittest.mock import MagicMock

from core.business_risk.models.business_risk_result import BusinessRiskResult
from core.business_risk.models.aspect_risk import AspectRisk
from core.business_risk.models.risk_level import RiskLevel

from core.recommendation.exceptions import RecommendationError, RecommendationGenerationError
from core.recommendation.knowledge.exceptions import KnowledgeBaseError
from core.recommendation.engine import RecommendationEngine
from core.recommendation.service import RecommendationService
from core.recommendation.knowledge.knowledge_base import RecommendationKnowledgeBase


def test_uninitialized_knowledge_base_recovery():
    """Milestone 10.4: Querying an uninitialized Knowledge Base raises KnowledgeBaseError gracefully."""
    kb = RecommendationKnowledgeBase()
    with pytest.raises(KnowledgeBaseError):
        kb.get_rules(aspect="QUALITY", risk_level="HIGH")


def test_corrupted_rule_or_dependency_error_recovery():
    """Milestone 10.4: Unexpected error inside dependency is safely wrapped into RecommendationGenerationError."""
    mock_interpreter = MagicMock()
    mock_interpreter.interpret.side_effect = ValueError("Corrupted rule schema or configuration")

    engine = RecommendationEngine(interpreter=mock_interpreter)

    valid_br = BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=80.0, level="HIGH"),
        delivery=AspectRisk(aspect="delivery", score=20.0, level="LOW"),
        trust=AspectRisk(aspect="trust", score=50.0, level="MEDIUM"),
        business_risk_index=70.0,
        business_risk_level=RiskLevel.HIGH,
    )

    with pytest.raises(RecommendationGenerationError) as exc_info:
        engine.generate_recommendation(valid_br)

    assert "Recommendation generation failed" in str(exc_info.value)


def test_null_input_error_recovery():
    """Milestone 10.4: Passing None to RecommendationService raises RecommendationGenerationError without crashing."""
    service = RecommendationService()

    with pytest.raises(RecommendationGenerationError):
        service.generate_recommendation(None)

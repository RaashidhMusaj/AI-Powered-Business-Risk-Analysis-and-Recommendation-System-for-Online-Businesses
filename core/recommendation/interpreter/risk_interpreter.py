"""
Risk Interpreter Component.
Interprets BusinessRiskResult metrics into structured RecommendationContext findings.
Stateless, thread-safe, and pure analytical interpretation (no recommendation generation).
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from core.business_risk.models.business_risk_result import BusinessRiskResult
from core.business_risk.models.aspect_risk import AspectRisk
from core.recommendation.dto.recommendation_context import RecommendationContext

logger = logging.getLogger(__name__)

# Standard Risk Ranking Weights (higher numeric weight = higher severity)
RISK_WEIGHT_MAPPING: Dict[str, int] = {
    "CRITICAL": 5,
    "HIGH": 4,
    "MEDIUM": 3,
    "LOW": 2,
    "VERY_LOW": 1,
}

# Configurable Priority Level Mappings
PRIORITY_MAPPING: Dict[str, str] = {
    "CRITICAL": "IMMEDIATE",
    "HIGH": "IMMEDIATE",
    "MEDIUM": "HIGH",
    "LOW": "NORMAL",
    "VERY_LOW": "NORMAL",
}

# Configurable Business Status Mappings
BUSINESS_STATUS_MAPPING: Dict[str, str] = {
    "CRITICAL": "CRITICAL",
    "HIGH": "CRITICAL",
    "MEDIUM": "WARNING",
    "LOW": "HEALTHY",
    "VERY_LOW": "HEALTHY",
}


def _clean_level_str(val: Any) -> str:
    """Helper normalizing Enum or string representations to plain uppercase level string (e.g. 'HIGH')."""
    if val is None:
        return "LOW"
    if hasattr(val, "value"):
        return str(val.value).upper()
    val_str = str(val)
    if "." in val_str:
        return val_str.split(".")[-1].upper()
    return val_str.upper()


@dataclass
class _RiskExtraction:
    """Internal container holding extracted risk data."""
    overall_level: str
    overall_score: float
    aspects: List[AspectRisk]


@dataclass
class _RiskInterpretation:
    """Internal container holding derived business interpretation results."""
    priority: str
    main_issue: Optional[str]
    secondary_issue: Optional[str]
    good_area: Optional[str]
    risk_summary: Dict[str, Any]
    interpreted_risks: Dict[str, Any]


class RiskInterpreter:
    """
    Analyzes BusinessRiskResult dimensions and computes intermediate risk context.
    Operates in 3 logical stages: Data Extraction -> Risk Ranking -> Business Interpretation.
    Stateless and thread-safe for multi-tenant executions.
    """

    def __init__(self):
        logger.info("Initializing RiskInterpreter component")

    def interpret(self, risk_result: BusinessRiskResult) -> RecommendationContext:
        """
        Transforms raw BusinessRiskResult into a structured RecommendationContext.
        
        :param risk_result: Raw BusinessRiskResult output from business risk engine.
        :return: Populated RecommendationContext ready for downstream selector and builder.
        """
        logger.info("Starting risk interpretation pipeline...")

        # Stage 1: Risk Data Extraction
        extraction = self._extract_risk_data(risk_result)

        # Stage 2: Risk Ranking
        ranked_aspects = self._rank_risks(extraction.aspects)

        # Stage 3: Business Interpretation
        interpretation = self._determine_interpretation(extraction.overall_level, ranked_aspects)

        # Stage 4: Context Construction
        context = self._build_context(risk_result, interpretation)
        
        logger.info(
            f"Risk interpretation complete. Status: {interpretation.interpreted_risks.get('businessStatus')}, "
            f"Priority: {interpretation.priority}, Main Issue: {interpretation.main_issue}"
        )
        return context

    def _extract_risk_data(self, risk_result: BusinessRiskResult) -> _RiskExtraction:
        """
        Extracts overall risk levels and aspect risks from BusinessRiskResult.
        """
        raw_level = getattr(risk_result, "business_risk_level", "LOW")
        overall_level = _clean_level_str(raw_level)
        overall_score = float(getattr(risk_result, "business_risk_index", 0.0))

        aspects: List[AspectRisk] = []
        for aspect_name in ["quality", "delivery", "trust"]:
            aspect_obj = getattr(risk_result, aspect_name, None)
            if aspect_obj:
                aspects.append(aspect_obj)
            else:
                # Fallback if aspect is missing
                aspects.append(AspectRisk(aspect=aspect_name, score=0.0, level="LOW"))

        return _RiskExtraction(
            overall_level=overall_level,
            overall_score=overall_score,
            aspects=aspects
        )

    def _rank_risks(self, aspects: List[AspectRisk]) -> List[AspectRisk]:
        """
        Ranks aspect risks descending by numeric severity weight and crisp score as tie-breaker.
        """
        def get_sort_key(aspect_risk: AspectRisk):
            level_str = _clean_level_str(aspect_risk.level)
            weight = RISK_WEIGHT_MAPPING.get(level_str, 0)
            score = float(aspect_risk.score)
            return (weight, score)

        return sorted(aspects, key=get_sort_key, reverse=True)

    def _determine_interpretation(self, overall_level: str, ranked_aspects: List[AspectRisk]) -> _RiskInterpretation:
        """
        Executes business interpretation logic to derive priorities, issues, and status metrics.
        """
        priority = self._determine_priority(overall_level)
        main_issue = self._determine_main_issue(ranked_aspects)
        secondary_issue = self._determine_secondary_issue(ranked_aspects, main_issue)
        good_area = self._determine_good_area(ranked_aspects)
        risk_summary = self._build_risk_summary(ranked_aspects)
        interpreted_risks = self._build_interpreted_risks(overall_level, main_issue)

        return _RiskInterpretation(
            priority=priority,
            main_issue=main_issue,
            secondary_issue=secondary_issue,
            good_area=good_area,
            risk_summary=risk_summary,
            interpreted_risks=interpreted_risks
        )

    def _determine_priority(self, overall_level: str) -> str:
        """
        Maps overall business risk level to priority action status.
        """
        return PRIORITY_MAPPING.get(overall_level, "NORMAL")

    def _determine_main_issue(self, ranked_aspects: List[AspectRisk]) -> Optional[str]:
        """
        Finds the primary risk issue. If all aspect risks are LOW or VERY_LOW, returns None.
        """
        if not ranked_aspects:
            return None

        highest = ranked_aspects[0]
        level_weight = RISK_WEIGHT_MAPPING.get(_clean_level_str(highest.level), 0)

        # If highest risk level is LOW (weight <= 2), there is no significant issue
        if level_weight <= 2:
            return None

        return str(highest.aspect).upper()

    def _determine_secondary_issue(
        self, ranked_aspects: List[AspectRisk], main_issue: Optional[str]
    ) -> Optional[str]:
        """
        Finds the secondary risk issue if applicable and severity is MEDIUM or higher.
        """
        if not main_issue or len(ranked_aspects) < 2:
            return None

        second = ranked_aspects[1]
        level_weight = RISK_WEIGHT_MAPPING.get(_clean_level_str(second.level), 0)

        if level_weight <= 2:
            return None

        return str(second.aspect).upper()

    def _determine_good_area(self, ranked_aspects: List[AspectRisk]) -> Optional[str]:
        """
        Identifies the best performing (lowest risk) business aspect.
        """
        if not ranked_aspects:
            return None

        lowest = ranked_aspects[-1]
        return str(lowest.aspect).upper()

    def _build_risk_summary(self, ranked_aspects: List[AspectRisk]) -> Dict[str, Any]:
        """
        Builds risk summary statistics including counts and boundary risk levels.
        """
        high_count = 0
        medium_count = 0
        low_count = 0

        for asp in ranked_aspects:
            lvl = _clean_level_str(asp.level)
            if lvl in ["HIGH", "CRITICAL"]:
                high_count += 1
            elif lvl == "MEDIUM":
                medium_count += 1
            else:
                low_count += 1

        highest_level = _clean_level_str(ranked_aspects[0].level) if ranked_aspects else "LOW"
        lowest_level = _clean_level_str(ranked_aspects[-1].level) if ranked_aspects else "LOW"

        return {
            "highRiskCount": high_count,
            "mediumRiskCount": medium_count,
            "lowRiskCount": low_count,
            "highestRiskLevel": highest_level,
            "lowestRiskLevel": lowest_level
        }

    def _build_interpreted_risks(
        self, overall_level: str, main_issue: Optional[str]
    ) -> Dict[str, Any]:
        """
        Builds interpreted risk metadata dictionary.
        """
        business_status = BUSINESS_STATUS_MAPPING.get(overall_level, "HEALTHY")
        primary_focus = main_issue if main_issue else "GENERAL_MAINTENANCE"

        return {
            "businessStatus": business_status,
            "primaryFocus": primary_focus,
            "confidence": None  # Honest placeholder until dynamic confidence calculation is added
        }

    def _build_context(
        self, risk_result: BusinessRiskResult, interpretation: _RiskInterpretation
    ) -> RecommendationContext:
        """
        Constructs and returns final RecommendationContext instance.
        """
        return RecommendationContext(
            business_risk_result=risk_result,
            priority=interpretation.priority,
            main_issue=interpretation.main_issue,
            secondary_issue=interpretation.secondary_issue,
            good_area=interpretation.good_area,
            interpreted_risks=interpretation.interpreted_risks,
            risk_summary=interpretation.risk_summary
        )

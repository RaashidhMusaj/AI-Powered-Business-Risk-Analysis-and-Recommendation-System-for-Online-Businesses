"""
Template Resolver Component.
Maps recommendation aspect, risk level, and priority metadata to template IDs cleanly.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TemplateResolver:
    """
    Resolves template IDs for summaries, insights, and actions dynamically.
    Decouples report assembly from template naming conventions.
    """

    def __init__(self):
        logger.info("Initializing TemplateResolver component")

    def resolve_summary(self, highest_priority: str, aspect: Optional[str] = None) -> str:
        """
        Resolves summary template ID based on priority and aspect.
        """
        prio_upper = str(highest_priority).upper()

        if prio_upper in ["IMMEDIATE", "HIGH"]:
            if aspect and aspect.upper() == "QUALITY":
                return "summary_high_quality"
            return "summary_high_quality"
        elif prio_upper in ["MEDIUM", "WARNING"]:
            return "summary_medium_risk"
        elif prio_upper == "NORMAL":
            if aspect and aspect.upper() == "GENERAL":
                return "summary_healthy_performance"
            return "summary_healthy_performance"

        return "summary_healthy_performance"

    def resolve_insight(self, aspect: str, risk_level: str) -> str:
        """
        Resolves insight template ID based on aspect and risk level.
        """
        asp_upper = str(aspect).upper()
        lvl_upper = str(risk_level).upper()

        if asp_upper == "QUALITY":
            return "insight_quality_high"
        elif asp_upper == "DELIVERY":
            return "insight_delivery_medium"
        elif asp_upper == "TRUST":
            return "insight_trust_high"

        return "insight_quality_high"

    def resolve_action(self, aspect: str, risk_level: str) -> str:
        """
        Resolves action template ID based on aspect and risk level.
        """
        asp_upper = str(aspect).upper()

        if asp_upper == "QUALITY":
            return "action_quality_high"
        elif asp_upper == "DELIVERY":
            return "action_delivery_high"
        elif asp_upper == "GENERAL":
            return "action_general_maintenance"

        return "action_quality_high"

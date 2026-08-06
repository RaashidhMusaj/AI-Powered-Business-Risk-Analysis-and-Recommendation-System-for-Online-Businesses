"""
Recommendation Context Data Transfer Object.
Holds evaluation state and derived risk insights for recommendation processing.
Stateless and completely decoupled from tenant/user authentication metadata.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from core.business_risk.models.business_risk_result import BusinessRiskResult

logger = logging.getLogger(__name__)


@dataclass
class RecommendationContext:
    """
    Context object holding input BusinessRiskResult and intermediate evaluation states.
    Completely decoupled from user, tenant, or product authentication details.
    """

    business_risk_result: BusinessRiskResult
    priority: str = "MEDIUM"
    main_issue: Optional[str] = None
    secondary_issue: Optional[str] = None
    good_area: Optional[str] = None
    interpreted_risks: Dict[str, Any] = field(default_factory=dict)
    risk_summary: Dict[str, Any] = field(default_factory=dict)
    selected_actions: List[str] = field(default_factory=list)
    selected_template_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

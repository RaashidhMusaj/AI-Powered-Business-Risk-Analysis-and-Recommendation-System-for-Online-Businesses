from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional


@dataclass(frozen=True)
class AnalysisHistory:
    """
    Immutable domain representation of an Analysis History entry.
    Uses version-safe dictionary snapshots for risk and recommendation outputs.
    """
    analysis_id: str
    user_id: str
    product_id: str
    timestamp: datetime
    delivery_risk: float
    quality_risk: float
    trust_risk: float
    business_risk_index: float
    delivery_level: str
    quality_level: str
    trust_level: str
    overall_level: str
    business_risk_snapshot: Dict[str, Any] = field(default_factory=dict)
    recommendation_snapshot: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert domain entity to serializable dictionary."""
        return {
            "analysisId": self.analysis_id,
            "userId": self.user_id,
            "productId": self.product_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "deliveryRisk": self.delivery_risk,
            "qualityRisk": self.quality_risk,
            "trustRisk": self.trust_risk,
            "businessRiskIndex": self.business_risk_index,
            "deliveryLevel": self.delivery_level,
            "qualityLevel": self.quality_level,
            "trustLevel": self.trust_level,
            "overallLevel": self.overall_level,
            "businessRiskSnapshot": self.business_risk_snapshot,
            "recommendationSnapshot": self.recommendation_snapshot,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }

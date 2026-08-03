from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from core.history.repository import AnalysisHistoryRepository
from core.history.exceptions import HistoryNotFoundError, ProductNotFoundError
from core.history.validator import HistoryValidator
from app.models.product import Product
from app.utils.logger import service_logger


class AnalysisHistoryService:
    """
    Business orchestration service for Historical Analysis, Trend Analytics, and Comparisons.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = AnalysisHistoryRepository(db)

    def save_analysis(
        self,
        public_id: str,
        user_id: UUID,
        product_id: UUID,
        business_risk_level: str,
        quality_risk_score: float,
        delivery_risk_score: float,
        trust_risk_score: float,
        overall_business_risk_index: float,
        business_risk_snapshot: Optional[Dict[str, Any]] = None,
        recommendation_snapshot: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Persists a completed analysis snapshot.
        """
        history_data = {
            "public_id": public_id,
            "user_id": user_id,
            "product_id": product_id,
            "business_risk_level": business_risk_level,
            "quality_risk_score": quality_risk_score,
            "delivery_risk_score": delivery_risk_score,
            "trust_risk_score": trust_risk_score,
            "overall_business_risk_index": overall_business_risk_index,
            "business_risk_snapshot": business_risk_snapshot or {},
            "recommendation_snapshot": recommendation_snapshot or {},
        }
        record = self.repo.save(history_data)
        return {
            "analysisId": record.public_id,
            "productId": str(record.product_id),
            "userId": str(record.user_id),
            "createdAt": record.created_at.isoformat() if record.created_at else None,
        }

    def get_latest_analysis(self, user_id: UUID, product_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Retrieves the latest analysis record for a user or product.
        """
        record = self.repo.find_latest(user_id=user_id, product_id=product_id)
        if not record:
            raise HistoryNotFoundError("No historical analysis records found.")
        return self._format_analysis_record(record)

    def get_analysis_history(self, user_id: UUID, product_id: Optional[UUID] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieves historical analysis runs for a user or product.
        """
        if product_id:
            records = self.repo.find_by_product(product_id=product_id, user_id=user_id)
        else:
            records = self.repo.find_by_user(user_id=user_id, limit=limit)
        return [self._format_analysis_record(r) for r in records]

    def get_trend_data(self, user_id: UUID, product_id: Any = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Returns chronological trend data formatted as an array of objects:
        [{"date": "2026-01-01", "delivery": 61, "quality": 55, "trust": 43, "bri": 56}]
        (Architectural Improvement #4 - Extensible Array of Objects)
        """
        target_prod_id = None
        if product_id and str(product_id).lower() != "all":
            try:
                target_prod_id = UUID(str(product_id)) if isinstance(product_id, str) else product_id
            except (ValueError, TypeError):
                target_prod_id = None

        if target_prod_id:
            records = self.repo.find_by_product(product_id=target_prod_id, user_id=user_id)
        else:
            records = self.repo.find_by_user(user_id=user_id, limit=limit)

        # Sort chronological (oldest to newest) for trend line plotting
        chronological = sorted(records, key=lambda x: x.created_at)

        trend_points = []
        for r in chronological:
            date_str = r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "N/A"
            trend_points.append({
                "date": date_str,
                "analysisId": r.public_id,
                "delivery": round(r.delivery_risk_score, 1),
                "quality": round(r.quality_risk_score, 1),
                "trust": round(r.trust_risk_score, 1),
                "bri": round(r.business_risk_index, 1),
                "riskLevel": r.business_risk_level,
            })
        return trend_points

    def compare_analyses(self, user_id: UUID, from_id: str, to_id: str) -> Dict[str, Any]:
        """
        Calculates side-by-side metric deltas between two analysis runs.
        (Architectural Improvement #6 - Comparative Delta Engine)
        """
        HistoryValidator.validate_comparison_ids(from_id, to_id)

        from_rec = self.repo.find_by_public_id(from_id, user_id)
        to_rec = self.repo.find_by_public_id(to_id, user_id)

        if not from_rec or not to_rec:
            raise HistoryNotFoundError("One or both analysis records for comparison could not be found.")

        del_delta = round(to_rec.delivery_risk_score - from_rec.delivery_risk_score, 1)
        qual_delta = round(to_rec.quality_risk_score - from_rec.quality_risk_score, 1)
        trust_delta = round(to_rec.trust_risk_score - from_rec.trust_risk_score, 1)
        bri_delta = round(to_rec.business_risk_index - from_rec.business_risk_index, 1)

        return {
            "fromAnalysisId": from_id,
            "toAnalysisId": to_id,
            "fromTimestamp": from_rec.created_at.isoformat() if from_rec.created_at else None,
            "toTimestamp": to_rec.created_at.isoformat() if to_rec.created_at else None,
            "deltas": {
                "delivery": del_delta,
                "quality": qual_delta,
                "trust": trust_delta,
                "bri": bri_delta,
            },
            "fromScores": {
                "delivery": round(from_rec.delivery_risk_score, 1),
                "quality": round(from_rec.quality_risk_score, 1),
                "trust": round(from_rec.trust_risk_score, 1),
                "bri": round(from_rec.business_risk_index, 1),
                "level": from_rec.business_risk_level,
            },
            "toScores": {
                "delivery": round(to_rec.delivery_risk_score, 1),
                "quality": round(to_rec.quality_risk_score, 1),
                "trust": round(to_rec.trust_risk_score, 1),
                "bri": round(to_rec.business_risk_index, 1),
                "level": to_rec.business_risk_level,
            }
        }

    def _format_analysis_record(self, r: Any) -> Dict[str, Any]:
        """Formats Analysis ORM instance for API output."""
        return {
            "analysisId": r.public_id,
            "productId": str(r.product_id),
            "productTitle": r.product.product_title if r.product else "Unknown Product",
            "productUrl": r.product.product_url if r.product else "",
            "platform": r.product.platform if r.product else "Daraz",
            "createdAt": r.created_at.isoformat() if r.created_at else None,
            "overallBusinessRiskIndex": r.business_risk_index,
            "businessRiskLevel": r.business_risk_level,
            "scores": {
                "quality": r.quality_risk_score,
                "delivery": r.delivery_risk_score,
                "trust": r.trust_risk_score,
            },
            "businessRiskSnapshot": r.business_risk_snapshot or {},
            "recommendationSnapshot": r.recommendation_snapshot or {},
        }

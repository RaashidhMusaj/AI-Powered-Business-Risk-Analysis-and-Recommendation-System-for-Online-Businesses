from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, or_

from app.models.analysis import Analysis
from app.models.product import Product
from core.history.models import AnalysisHistory
from app.utils.logger import db_logger


class AnalysisHistoryRepository:
    """
    Persistence repository for AnalysisHistory entries with tenant isolation.
    """

    def __init__(self, db: Session):
        self.db = db

    def save(self, history_data: dict) -> Analysis:
        """
        Saves a new analysis record to the database.
        """
        analysis = Analysis(
            public_id=history_data.get("public_id"),
            user_id=history_data.get("user_id"),
            product_id=history_data.get("product_id"),
            business_risk_level=history_data.get("business_risk_level", "UNKNOWN"),
            quality_risk_score=history_data.get("quality_risk_score", 0.0),
            delivery_risk_score=history_data.get("delivery_risk_score", 0.0),
            trust_risk_score=history_data.get("trust_risk_score", 0.0),
            business_risk_index=history_data.get("overall_business_risk_index", 0.0),
            business_risk_snapshot=history_data.get("business_risk_snapshot"),
            recommendation_snapshot=history_data.get("recommendation_snapshot"),
        )
        self.db.add(analysis)
        self.db.flush()
        db_logger.info(f"AnalysisHistory saved with public_id={analysis.public_id}")
        return analysis

    def find_latest(self, user_id: UUID, product_id: Optional[UUID] = None) -> Optional[Analysis]:
        """
        Finds the most recent analysis record for a user or specific product.
        """
        stmt = (
            select(Analysis)
            .options(joinedload(Analysis.product))
            .where(Analysis.user_id == user_id)
        )
        if product_id is not None:
            stmt = stmt.where(Analysis.product_id == product_id)

        stmt = stmt.order_by(Analysis.created_at.desc())
        return self.db.scalars(stmt).first()

    def find_by_product(self, product_id: UUID, user_id: UUID) -> List[Analysis]:
        """
        Finds all analysis history records for a specific product, newest first.
        """
        stmt = (
            select(Analysis)
            .options(joinedload(Analysis.product))
            .where(Analysis.product_id == product_id, Analysis.user_id == user_id)
            .order_by(Analysis.created_at.desc())
        )
        return list(self.db.scalars(stmt).unique().all())

    def find_by_user(self, user_id: UUID, limit: int = 50) -> List[Analysis]:
        """
        Finds all analysis history records for a user, newest first.
        """
        stmt = (
            select(Analysis)
            .options(joinedload(Analysis.product))
            .where(Analysis.user_id == user_id)
            .order_by(Analysis.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).unique().all())

    def find_by_public_id(self, public_id: str, user_id: UUID) -> Optional[Analysis]:
        """
        Finds a specific analysis record by public ID (anl_...).
        """
        stmt = (
            select(Analysis)
            .options(joinedload(Analysis.product), joinedload(Analysis.reviews))
            .where(Analysis.public_id == public_id, Analysis.user_id == user_id)
        )
        return self.db.scalars(stmt).first()

    def delete(self, public_id: str, user_id: UUID) -> bool:
        """
        Deletes an analysis record for a user.
        """
        record = self.find_by_public_id(public_id, user_id)
        if not record:
            return False
        self.db.delete(record)
        self.db.flush()
        return True

    def count(self, user_id: UUID, product_id: Optional[UUID] = None) -> int:
        """
        Counts total analysis runs for user/product.
        """
        stmt = select(func.count(Analysis.id)).where(Analysis.user_id == user_id)
        if product_id is not None:
            stmt = stmt.where(Analysis.product_id == product_id)
        return self.db.scalar(stmt) or 0

    def exists(self, public_id: str) -> bool:
        """
        Checks if an analysis public_id exists.
        """
        stmt = select(func.count(Analysis.id)).where(Analysis.public_id == public_id)
        return (self.db.scalar(stmt) or 0) > 0

from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.review import Review
from app.utils.logger import db_logger


class ReviewRepository:
    """
    Encapsulates database operations for processed Review entities.
    """
    def __init__(self, db: Session):
        self.db = db

    def bulk_add(self, reviews: List[Review]) -> List[Review]:
        """
        Bulk adds review entities to session.
        """
        if not reviews:
            return []

        db_logger.info(f"Bulk adding {len(reviews)} review records")
        self.db.add_all(reviews)
        self.db.flush()
        return reviews

    def get_by_analysis_id(self, analysis_id_uuid: UUID) -> List[Review]:
        """
        Retrieves reviews associated with an analysis internal UUID.
        """
        stmt = select(Review).where(Review.analysis_id == analysis_id_uuid)
        return list(self.db.scalars(stmt).all())

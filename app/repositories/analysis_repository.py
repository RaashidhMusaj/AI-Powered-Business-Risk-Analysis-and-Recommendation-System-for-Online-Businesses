from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, delete, or_

from app.models.analysis import Analysis
from app.models.product import Product
from app.utils.logger import db_logger


class AnalysisRepository:
    """
    Encapsulates database queries and persistence for Analysis entities with tenant isolation.
    """

    def __init__(self, db: Session):
        self.db = db

    def add(self, analysis: Analysis) -> Analysis:
        """
        Adds a new Analysis entity to session.
        """
        db_logger.info(f"Adding analysis record with public_id={analysis.public_id} for user_id={analysis.user_id}")
        self.db.add(analysis)
        self.db.flush()
        return analysis

    def get_by_public_id(self, public_id: str, user_id: Optional[UUID] = None) -> Optional[Analysis]:
        """
        Retrieves analysis by public business identifier (anl_...).
        Scoped to user_id if provided. Eagerly loads related Product and Reviews.
        """
        stmt = (
            select(Analysis)
            .options(joinedload(Analysis.product), joinedload(Analysis.reviews))
            .where(Analysis.public_id == public_id)
        )
        if user_id is not None:
            stmt = stmt.where(Analysis.user_id == user_id)

        return self.db.scalars(stmt).first()

    def delete_by_public_id(self, public_id: str, user_id: Optional[UUID] = None) -> bool:
        """
        Deletes an analysis record by public business identifier (anl_...).
        Scoped to user_id if provided. Cascades deletion to related reviews.
        """
        analysis = self.get_by_public_id(public_id, user_id=user_id)
        if not analysis:
            return False

        db_logger.info(f"Deleting analysis record public_id={public_id} for user_id={user_id}")
        self.db.delete(analysis)
        self.db.flush()
        return True

    def list_paginated(
        self,
        user_id: UUID,
        page: int = 1,
        limit: int = 10,
        risk_level: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> Tuple[List[Analysis], int]:
        """
        Retrieves user-scoped paginated history with filtering, searching, and sorting.
        """
        stmt = (
            select(Analysis)
            .join(Analysis.product)
            .options(joinedload(Analysis.product))
            .where(Analysis.user_id == user_id)
        )

        # Filter by Business Risk Level
        if risk_level:
            stmt = stmt.where(Analysis.business_risk_level == risk_level.upper())

        # Search by Product Title or Public ID
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Product.product_title.ilike(search_pattern),
                    Analysis.public_id.ilike(search_pattern),
                )
            )

        # Total matching records count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        # Sorting
        sort_column = getattr(Analysis, sort_by, Analysis.created_at)
        if order.lower() == "asc":
            stmt = stmt.order_by(sort_column.asc())
        else:
            stmt = stmt.order_by(sort_column.desc())

        # Pagination Offset
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)

        items = list(self.db.scalars(stmt).unique().all())
        return items, total

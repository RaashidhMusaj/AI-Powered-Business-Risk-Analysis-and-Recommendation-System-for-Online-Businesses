from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.product import Product
from app.utils.logger import db_logger


class ProductRepository:
    """
    Encapsulates database operations for Product entities with tenant isolation and global URL lookup.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_by_url(self, product_url: str, user_id: Optional[UUID] = None) -> Optional[Product]:
        """
        Retrieves product by URL. Checks user-owned product first, then falls back to global URL match
        to prevent UniqueViolation on product_url constraint when multiple users analyze the same item.
        """
        if user_id is not None:
            user_stmt = select(Product).where(Product.product_url == product_url, Product.user_id == user_id)
            user_prod = self.db.scalars(user_stmt).first()
            if user_prod:
                return user_prod

        global_stmt = select(Product).where(Product.product_url == product_url)
        return self.db.scalars(global_stmt).first()

    def add(self, product: Product) -> Product:
        """
        Adds a new Product entity to the session.
        """
        db_logger.info(f"Adding product record for URL: {product.product_url} (user_id={product.user_id})")
        self.db.add(product)
        self.db.flush()
        return product

    def list_paginated(self, user_id: UUID, page: int = 1, limit: int = 10) -> Tuple[List[Product], int]:
        """
        Retrieves paginated list of analyzed products for a specific user ordered by most recent.
        """
        total_stmt = select(func.count(Product.id)).where(Product.user_id == user_id)
        total = self.db.scalar(total_stmt) or 0

        offset = (page - 1) * limit
        stmt = (
            select(Product)
            .where(Product.user_id == user_id)
            .order_by(Product.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list(self.db.scalars(stmt).all())

        return items, total

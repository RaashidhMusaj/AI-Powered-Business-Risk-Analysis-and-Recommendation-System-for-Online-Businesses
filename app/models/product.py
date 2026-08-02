from sqlalchemy import Column, String, Float, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database.base import BaseEntity, UUIDType


class Product(BaseEntity):
    """
    Product ORM Model storing platform product metadata with tenant ownership.
    """
    __tablename__ = "products"
    __table_args__ = (
        Index("idx_products_user_created", "user_id", "created_at"),
    )

    user_id = Column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    product_url = Column(String(2048), index=True, nullable=False)
    product_title = Column(String(512), nullable=False)
    platform = Column(String(64), default="Daraz", nullable=False)
    category = Column(String(512), nullable=True)
    overall_rating = Column(Float, default=0.0, nullable=False)
    total_reviews = Column(Integer, default=0, nullable=False)
    seller_name = Column(String(256), nullable=True)
    image_url = Column(String(2048), nullable=True)

    # Relationships
    user = relationship("User", back_populates="products")
    analyses = relationship(
        "Analysis",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="desc(Analysis.created_at)"
    )

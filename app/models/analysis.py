from sqlalchemy import Column, String, Float, Integer, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database.base import BaseEntity, UUIDType


class Analysis(BaseEntity):
    """
    Analysis ORM Model storing complete risk analysis execution result metrics with tenant ownership.
    """
    __tablename__ = "analyses"
    __table_args__ = (
        Index("idx_analyses_user_created", "user_id", "created_at"),
        Index("idx_analyses_user_risk_level", "user_id", "business_risk_level"),
    )

    public_id = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id = Column(UUIDType, ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False)

    status = Column(String(32), default="completed", nullable=False)
    execution_duration_ms = Column(Float, default=0.0, nullable=False)

    # Fuzzy Risk Scores & Business Risk Index
    quality_risk_score = Column(Float, default=0.0, nullable=False)
    delivery_risk_score = Column(Float, default=0.0, nullable=False)
    trust_risk_score = Column(Float, default=0.0, nullable=False)
    business_risk_index = Column(Float, index=True, default=0.0, nullable=False)
    business_risk_level = Column(String(32), index=True, nullable=False)

    # First-Class SQL Metric Columns
    total_reviews = Column(Integer, default=0, nullable=False)
    total_positive_reviews = Column(Integer, default=0, nullable=False)
    total_negative_reviews = Column(Integer, default=0, nullable=False)
    total_neutral_reviews = Column(Integer, default=0, nullable=False)
    average_confidence = Column(Float, default=0.0, nullable=False)

    # Dynamic JSON Breakdown Columns
    aspect_statistics = Column(JSON, nullable=True)
    confidence_statistics = Column(JSON, nullable=True)
    risk_breakdown = Column(JSON, nullable=True)
    business_risk_snapshot = Column(JSON, nullable=True)
    recommendation_snapshot = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="analyses")
    product = relationship("Product", back_populates="analyses")
    reviews = relationship(
        "Review",
        back_populates="analysis",
        cascade="all, delete-orphan"
    )

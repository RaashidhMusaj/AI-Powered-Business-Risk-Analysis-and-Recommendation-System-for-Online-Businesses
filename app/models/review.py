from sqlalchemy import Column, Text, String, Float, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database.base import BaseEntity, UUIDType


class Review(BaseEntity):
    """
    Review ORM Model storing individual processed customer reviews with tenant ownership.
    """
    __tablename__ = "reviews"
    __table_args__ = (
        Index("idx_reviews_user_analysis", "user_id", "analysis_id"),
    )

    user_id = Column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    analysis_id = Column(UUIDType, ForeignKey("analyses.id", ondelete="CASCADE"), index=True, nullable=False)

    review_text = Column(Text, nullable=False)
    sentiment = Column(String(32), index=True, nullable=True)
    confidence_score = Column(Float, default=0.0, nullable=False)
    aspects = Column(JSON, nullable=True)
    language = Column(String(32), nullable=True)
    preprocessing_metadata = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User")
    analysis = relationship("Analysis", back_populates="reviews")

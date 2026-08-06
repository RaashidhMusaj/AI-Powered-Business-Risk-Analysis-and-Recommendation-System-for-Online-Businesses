from sqlalchemy import Column, String, Boolean, Integer, DateTime
from sqlalchemy.orm import relationship

from app.database.base import BaseEntity


class User(BaseEntity):
    """
    User ORM Model storing tenant account credentials and profile metadata.
    """
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(64), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(128), nullable=True)
    role = Column(String(32), default="seller", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    reset_otp_code = Column(String(16), nullable=True, index=True)
    reset_otp_expires_at = Column(DateTime, nullable=True)

    # Relationships
    products = relationship(
        "Product",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    analyses = relationship(
        "Analysis",
        back_populates="user",
        cascade="all, delete-orphan"
    )

from sqlalchemy import Column, String, Boolean
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
    is_active = Column(Boolean, default=True, nullable=False)

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

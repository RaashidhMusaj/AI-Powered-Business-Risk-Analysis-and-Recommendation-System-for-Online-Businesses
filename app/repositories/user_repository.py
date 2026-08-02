from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.models.user import User
from app.utils.logger import db_logger


class UserRepository:
    """
    Encapsulates all database operations for User entities.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        return self.db.scalars(stmt).first()

    def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email.lower().strip())
        return self.db.scalars(stmt).first()

    def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username.lower().strip())
        return self.db.scalars(stmt).first()

    def get_by_email_or_username(self, identifier: str) -> Optional[User]:
        clean_id = identifier.lower().strip()
        stmt = select(User).where(
            or_(User.email == clean_id, User.username == clean_id)
        )
        return self.db.scalars(stmt).first()

    def create(self, user: User) -> User:
        db_logger.info(f"Creating user record for email: {user.email}")
        self.db.add(user)
        self.db.flush()
        return user

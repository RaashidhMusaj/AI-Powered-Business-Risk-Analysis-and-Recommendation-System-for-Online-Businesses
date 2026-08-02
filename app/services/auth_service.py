from typing import Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import status

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.security.password import hash_password, verify_password
from app.security.jwt import create_access_token
from app.utils.exceptions import BaseBusinessException
from app.api.schemas.auth_schema import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenDataResponse,
    UserProfileResponse,
)


class UserAlreadyExistsError(BaseBusinessException):
    def __init__(self, message: str = "A user with this email or username already exists."):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)


class InvalidCredentialsError(BaseBusinessException):
    def __init__(self, message: str = "Invalid email/username or password."):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED)


class AuthService:
    """
    Business Service handling user registration, authentication, and JWT token issuance.
    """
    def __init__(self, db: Session, user_repo: UserRepository = None):
        self.db = db
        self.user_repo = user_repo or UserRepository(db)

    def register_user(self, schema: UserRegisterRequest) -> TokenDataResponse:
        # Check if email exists
        if self.user_repo.get_by_email(schema.email):
            raise UserAlreadyExistsError("An account with this email address already exists.")

        # Check if username exists
        if self.user_repo.get_by_username(schema.username):
            raise UserAlreadyExistsError("This username is already taken.")

        hashed_pwd = hash_password(schema.password)
        new_user = User(
            email=schema.email.lower().strip(),
            username=schema.username.lower().strip(),
            hashed_password=hashed_pwd,
            full_name=schema.fullName,
            is_active=True,
        )

        created_user = self.user_repo.create(new_user)
        self.db.commit()
        self.db.refresh(created_user)

        token = create_access_token(data={"sub": str(created_user.id), "username": created_user.username})

        return TokenDataResponse(
            accessToken=token,
            tokenType="bearer",
            userId=str(created_user.id),
            username=created_user.username,
            email=created_user.email,
        )

    def authenticate_user(self, schema: UserLoginRequest) -> TokenDataResponse:
        user = self.user_repo.get_by_email_or_username(schema.emailOrUsername)
        if not user or not verify_password(schema.password, user.hashed_password):
            raise InvalidCredentialsError("Invalid username/email or password.")

        if not user.is_active:
            raise InvalidCredentialsError("Account is inactive.")

        token = create_access_token(data={"sub": str(user.id), "username": user.username})

        return TokenDataResponse(
            accessToken=token,
            tokenType="bearer",
            userId=str(user.id),
            username=user.username,
            email=user.email,
        )

    def get_user_profile(self, user_id: UUID) -> UserProfileResponse:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise InvalidCredentialsError("User account not found.")

        return UserProfileResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            fullName=user.full_name,
            isActive=user.is_active,
            createdAt=user.created_at.isoformat() if user.created_at else "",
        )

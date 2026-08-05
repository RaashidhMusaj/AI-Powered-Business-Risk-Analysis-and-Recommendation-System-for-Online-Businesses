from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import status

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.security.password import hash_password, verify_password
from app.security.jwt import create_access_token
from app.utils.exceptions import BaseBusinessException
from app.utils.logger import api_logger
from app.api.schemas.auth_schema import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenDataResponse,
    UserProfileResponse,
)

MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


class UserAlreadyExistsError(BaseBusinessException):
    def __init__(self, message: str = "A user with this email or username already exists."):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)


class InvalidCredentialsError(BaseBusinessException):
    def __init__(self, message: str = "Invalid email/username or password."):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED)


class AccountLockedError(BaseBusinessException):
    def __init__(self, message: str = "Account is temporarily locked due to excessive failed attempts. Please try again in 15 minutes."):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED)


class AuthService:
    """
    Business Service handling user registration, authentication, account lockout, and JWT token issuance.
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
        user_role = (schema.role or "seller").lower().strip()
        new_user = User(
            email=schema.email.lower().strip(),
            username=schema.username.lower().strip(),
            hashed_password=hashed_pwd,
            full_name=schema.fullName,
            role=user_role,
            is_active=True,
            failed_login_attempts=0,
            locked_until=None,
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
            role=created_user.role or "seller",
        )

    def authenticate_user(self, schema: UserLoginRequest) -> TokenDataResponse:
        user = self.user_repo.get_by_email_or_username(schema.emailOrUsername)
        if not user:
            raise InvalidCredentialsError("Invalid username/email or password.")

        if not user.is_active:
            raise InvalidCredentialsError("Account is inactive.")

        now_utc = datetime.now(timezone.utc)

        # Check account lockout status
        if user.locked_until:
            locked_until = user.locked_until
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)

            if now_utc < locked_until:
                remaining_mins = max(1, int((locked_until - now_utc).total_seconds() // 60))
                raise AccountLockedError(f"Account is temporarily locked due to excessive failed attempts. Please try again in {remaining_mins} minutes.")
            else:
                # Lockout expired -> reset counter
                user.failed_login_attempts = 0
                user.locked_until = None
                self.db.commit()

        if not verify_password(schema.password, user.hashed_password):
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
                user.locked_until = now_utc + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                self.db.commit()
                api_logger.warning(f"Account locked for username [{user.username}] after {user.failed_login_attempts} failed login attempts.")
                raise AccountLockedError(f"Account is temporarily locked due to excessive failed attempts. Please try again in {LOCKOUT_DURATION_MINUTES} minutes.")

            self.db.commit()
            raise InvalidCredentialsError("Invalid username/email or password.")

        # Reset failed login attempt counter on successful login
        if user.failed_login_attempts > 0 or user.locked_until is not None:
            user.failed_login_attempts = 0
            user.locked_until = None
            self.db.commit()

        token = create_access_token(data={"sub": str(user.id), "username": user.username})

        return TokenDataResponse(
            accessToken=token,
            tokenType="bearer",
            userId=str(user.id),
            username=user.username,
            email=user.email,
            role=user.role or "seller",
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
            role=user.role or "seller",
            isActive=user.is_active,
            createdAt=user.created_at.isoformat() if user.created_at else "",
        )

    def request_password_reset(self, email: str) -> Dict[str, Any]:
        """
        Generates 6-digit OTP verification code, saves 15-min expiration to DB, and dispatches via email service.
        """
        import secrets
        from app.services.email_service import send_otp_email

        user = self.user_repo.get_by_email(email.strip().lower())
        if not user:
            # Generic response for security to prevent email enumeration
            return {
                "message": f"If an account exists for {email}, a 6-digit verification code has been dispatched.",
                "email": email,
                "sent": True,
            }

        # Generate 6-digit numeric OTP code
        otp_code = str(secrets.randbelow(900000) + 100000)
        now_utc = datetime.now(timezone.utc)
        user.reset_otp_code = otp_code
        user.reset_otp_expires_at = now_utc + timedelta(minutes=15)
        self.db.commit()

        sent_via_email, msg = send_otp_email(user.email, otp_code)

        return {
            "message": msg,
            "email": user.email,
            "sent": sent_via_email,
            "otpCode": otp_code if not sent_via_email else None,  # Provided for instant UI demo mode testing when offline
        }

    def reset_password_with_otp(self, email: str, otp_code: str, new_password: str) -> TokenDataResponse:
        """
        Verifies 6-digit OTP code & expiration, updates hashed password via bcrypt, unlocks account, and issues new JWT token.
        """
        user = self.user_repo.get_by_email(email.strip().lower())
        if not user:
            raise BaseBusinessException("Invalid email address or verification code.", status_code=status.HTTP_400_BAD_REQUEST)

        now_utc = datetime.now(timezone.utc)

        if not user.reset_otp_code or user.reset_otp_code.strip() != otp_code.strip():
            raise BaseBusinessException("Invalid verification code. Please check your code and try again.", status_code=status.HTTP_400_BAD_REQUEST)

        if not user.reset_otp_expires_at:
            raise BaseBusinessException("Verification code has expired. Please request a new one.", status_code=status.HTTP_400_BAD_REQUEST)

        expires_at = user.reset_otp_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if now_utc > expires_at:
            raise BaseBusinessException("Verification code has expired. Please request a new code.", status_code=status.HTTP_400_BAD_REQUEST)

        # Update password, reset lockout and clear OTP
        user.hashed_password = hash_password(new_password)
        user.reset_otp_code = None
        user.reset_otp_expires_at = None
        user.failed_login_attempts = 0
        user.locked_until = None
        self.db.commit()

        token = create_access_token(data={"sub": str(user.id), "username": user.username})

        return TokenDataResponse(
            accessToken=token,
            tokenType="bearer",
            userId=str(user.id),
            username=user.username,
            email=user.email,
            role=user.role or "seller",
        )

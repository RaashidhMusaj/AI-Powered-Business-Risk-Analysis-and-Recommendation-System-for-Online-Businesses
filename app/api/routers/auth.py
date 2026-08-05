from fastapi import APIRouter, Depends, Request, status
from datetime import datetime, timezone

from app.api.schemas.common_schema import ApiResponse, ApiMeta
from app.api.schemas.auth_schema import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenDataResponse,
    ForgotPasswordRequest,
    ResetPasswordWithOTPRequest,
)
from app.services.auth_service import AuthService
from app.api.dependencies.services import get_auth_service
from app.constants.api_constants import APIConstants
from app.config.settings import settings

router = APIRouter(prefix="/v1/auth", tags=[APIConstants.TAG_AUTH])


@router.post("/register", response_model=ApiResponse[TokenDataResponse], summary="User Registration")
async def register(
    request: Request,
    body: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Registers a new tenant user account and returns a JWT access token.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    token_data = auth_service.register_user(body)

    return ApiResponse(
        success=True,
        message="User account registered successfully.",
        data=token_data,
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION,
        ),
    )


@router.post("/login", response_model=ApiResponse[TokenDataResponse], summary="User Login")
async def login(
    request: Request,
    body: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Authenticates user credentials and issues a JWT access token.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    token_data = auth_service.authenticate_user(body)

    return ApiResponse(
        success=True,
        message="Login successful.",
        data=token_data,
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION,
        ),
    )


@router.post("/forgot-password", summary="Request 6-Digit Password Reset OTP")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Generates a 6-digit OTP verification code and dispatches it via email service (with local demo fallback).
    """
    request_id = getattr(request.state, "request_id", "unknown")
    result = auth_service.request_password_reset(body.email)

    return ApiResponse(
        success=True,
        message=result["message"],
        data=result,
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION,
        ),
    )


@router.post("/reset-password", response_model=ApiResponse[TokenDataResponse], summary="Reset Password with OTP")
async def reset_password(
    request: Request,
    body: ResetPasswordWithOTPRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Verifies 6-digit OTP code, resets password to new bcrypt hash, unlocks account, and issues new JWT token.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    token_data = auth_service.reset_password_with_otp(body.email, body.otpCode, body.newPassword)

    return ApiResponse(
        success=True,
        message="Password updated successfully. Account unlocked.",
        data=token_data,
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION,
        ),
    )

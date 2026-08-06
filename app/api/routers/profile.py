from fastapi import APIRouter, Depends, Request
from datetime import datetime, timezone

from app.api.schemas.common_schema import ApiResponse, ApiMeta
from app.api.schemas.auth_schema import UserProfileResponse
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.constants.api_constants import APIConstants
from app.config.settings import settings

router = APIRouter(prefix="/v1/profile", tags=[APIConstants.TAG_PROFILE])


@router.get("", response_model=ApiResponse[UserProfileResponse], summary="Get Current User Profile")
async def get_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    Returns profile information for the currently authenticated user.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    profile = UserProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        fullName=current_user.full_name,
        isActive=current_user.is_active,
        createdAt=current_user.created_at.isoformat() if current_user.created_at else "",
    )

    return ApiResponse(
        success=True,
        message="User profile retrieved successfully.",
        data=profile,
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION,
        ),
    )

from fastapi import APIRouter, Depends, Request
from datetime import datetime, timezone

from app.api.schemas.common_schema import ApiResponse, ApiMeta
from app.api.schemas.health_schema import HealthCheckResponse, VersionResponse
from app.services.health_service import HealthService
from app.api.dependencies.services import get_health_service
from app.constants.api_constants import APIConstants
from app.constants.messages import APIMessages
from app.config.settings import settings

router = APIRouter(tags=[APIConstants.TAG_SYSTEM])


@router.get("/health", response_model=ApiResponse[HealthCheckResponse], summary="System Health Check")
@router.get("/v1/health", response_model=ApiResponse[HealthCheckResponse], include_in_schema=False)
async def health_check(
    request: Request,
    health_service: HealthService = Depends(get_health_service)
):
    """
    Checks application running status, database connection, AI engine model loading state, and scraper status.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    health_data = health_service.get_health_status()
    
    return ApiResponse(
        success=health_data["status"] == "healthy",
        message=APIMessages.SUCCESS_HEALTH_CHECK,
        data=HealthCheckResponse(**health_data),
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION
        )
    )


@router.get("/version", response_model=ApiResponse[VersionResponse], summary="Application Version")
@router.get("/v1/version", response_model=ApiResponse[VersionResponse], include_in_schema=False)
async def version_check(
    request: Request,
    health_service: HealthService = Depends(get_health_service)
):
    """
    Returns application metadata, version, and environment.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    version_data = health_service.get_version_info()
    
    return ApiResponse(
        success=True,
        message=APIMessages.SUCCESS_VERSION_CHECK,
        data=VersionResponse(**version_data),
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION
        )
    )

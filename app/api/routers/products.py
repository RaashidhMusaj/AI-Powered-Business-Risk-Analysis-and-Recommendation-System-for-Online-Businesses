import math
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, Query

from app.api.schemas.common_schema import ApiResponse, ApiMeta
from app.api.schemas.history_schema import ProductListResponse, ProductItemResponse, PaginationMeta
from app.services.analysis_service import AnalysisService
from app.api.dependencies.services import get_analysis_service
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.constants.api_constants import APIConstants
from app.config.settings import settings

router = APIRouter(prefix="/v1/products", tags=[APIConstants.TAG_ANALYSIS])


@router.get("", response_model=ApiResponse[ProductListResponse], summary="Get Paginated Analyzed Products")
async def get_products(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Retrieves a paginated list of analyzed products for current authenticated user.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    products, total = service.get_products_paginated(user_id=current_user.id, page=page, limit=limit)

    total_pages = math.ceil(total / limit) if total > 0 else 0

    items = [
        ProductItemResponse(
            id=str(p.id),
            productUrl=p.product_url,
            productTitle=p.product_title,
            platform=p.platform,
            category=p.category,
            overallRating=p.overall_rating,
            totalReviews=p.total_reviews,
            createdAt=p.created_at.isoformat() if p.created_at else "",
        )
        for p in products
    ]

    response_payload = ProductListResponse(
        items=items,
        pagination=PaginationMeta(
            page=page,
            limit=limit,
            totalItems=total,
            totalPages=total_pages,
        ),
    )

    return ApiResponse(
        success=True,
        message="Analyzed products retrieved successfully.",
        data=response_payload,
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION,
        ),
    )

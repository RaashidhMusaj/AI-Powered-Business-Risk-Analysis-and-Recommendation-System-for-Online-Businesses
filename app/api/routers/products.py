import math
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Request, Query, HTTPException, status

from app.api.schemas.common_schema import ApiResponse, ApiMeta
from app.api.schemas.history_schema import ProductListResponse, ProductItemResponse, PaginationMeta
from app.services.analysis_service import AnalysisService
from app.api.dependencies.services import get_analysis_service
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.models.product import Product
from core.history.service import AnalysisHistoryService
from core.history.exceptions import HistoryNotFoundError, InvalidProductOwnershipError
from app.constants.api_constants import APIConstants
from app.config.settings import settings

router = APIRouter(prefix="/v1/products", tags=[APIConstants.TAG_ANALYSIS])


@router.get("", response_model=ApiResponse[ProductListResponse], summary="Get Paginated User Monitored Products")
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
        message="Monitored products retrieved successfully.",
        data=response_payload,
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION,
        ),
    )


@router.get("/{product_id}", summary="Get Product Details")
async def get_product_detail(
    product_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Retrieves specific product metadata for the authenticated user.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    product = service.db.query(Product).filter(Product.id == product_id, Product.user_id == current_user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or access denied.")

    return ApiResponse(
        success=True,
        message="Product details retrieved successfully.",
        data={
            "id": str(product.id),
            "productUrl": product.product_url,
            "productTitle": product.product_title,
            "platform": product.platform,
            "category": product.category,
            "overallRating": product.overall_rating,
            "totalReviews": product.total_reviews,
            "sellerName": product.seller_name,
            "imageUrl": product.image_url,
            "externalProductId": product.external_product_id,
            "currentPrice": product.current_price,
            "createdAt": product.created_at.isoformat() if product.created_at else "",
        },
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION,
        ),
    )


@router.get("/{product_id}/history", summary="Get Product Analysis History")
async def get_product_history(
    product_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Retrieves complete chronological analysis history for a specific product.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    history_service = AnalysisHistoryService(service.db)
    history_items = history_service.get_analysis_history(user_id=current_user.id, product_id=product_id)

    return ApiResponse(
        success=True,
        message="Product analysis history retrieved successfully.",
        data=history_items,
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION,
        ),
    )


@router.get("/{product_id}/latest", summary="Get Product Latest Analysis")
async def get_product_latest(
    product_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Retrieves the most recent analysis run for a product.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    history_service = AnalysisHistoryService(service.db)
    try:
        latest = history_service.get_latest_analysis(user_id=current_user.id, product_id=product_id)
    except HistoryNotFoundError:
        raise HTTPException(status_code=404, detail="No historical analysis found for this product.")

    return ApiResponse(
        success=True,
        message="Latest product analysis retrieved successfully.",
        data=latest,
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION,
        ),
    )


@router.get("/{product_id}/trend", summary="Get Product Risk Trend Dataset")
async def get_product_trend(
    product_id: str,
    request: Request,
    limit: int = Query(20, ge=2, le=100),
    current_user: User = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Returns historical time-series trend points formatted as an array of objects:
    [{"date": "2026-01-01", "delivery": 61, "quality": 55, "trust": 43, "bri": 56}]
    """
    request_id = getattr(request.state, "request_id", "unknown")
    history_service = AnalysisHistoryService(service.db)
    trend_data = history_service.get_trend_data(user_id=current_user.id, product_id=product_id, limit=limit)

    return ApiResponse(
        success=True,
        message="Product trend dataset retrieved successfully.",
        data=trend_data,
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION,
        ),
    )


@router.get("/{product_id}/compare", summary="Compare Two Historical Analysis Runs")
async def compare_product_analyses(
    product_id: str,
    request: Request,
    from_id: str = Query(..., alias="from", description="Base analysis public ID"),
    to_id: str = Query(..., alias="to", description="Target analysis public ID"),
    current_user: User = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Calculates side-by-side metric deltas between two historical analysis runs.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    history_service = AnalysisHistoryService(service.db)
    try:
        comparison = history_service.compare_analyses(user_id=current_user.id, from_id=from_id, to_id=to_id)
    except HistoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ApiResponse(
        success=True,
        message="Analysis comparison deltas calculated successfully.",
        data=comparison,
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION,
        ),
    )

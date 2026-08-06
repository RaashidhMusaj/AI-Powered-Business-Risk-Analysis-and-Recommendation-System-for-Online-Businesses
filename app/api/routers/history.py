import math
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, status
from fastapi.responses import JSONResponse

from app.api.schemas.common_schema import ApiResponse, ApiMeta
from app.api.schemas.history_schema import (
    HistoryListResponse,
    HistoryItemResponse,
    AnalysisDetailResponse,
    ReviewSummaryResponse,
    PaginationMeta,
)
from app.services.analysis_service import AnalysisService
from app.mappers.analysis_mapper import AnalysisMapper
from app.api.dependencies.services import get_analysis_service
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.constants.api_constants import APIConstants
from app.config.settings import settings

router = APIRouter(prefix="/v1/history", tags=[APIConstants.TAG_HISTORY])


@router.get("", response_model=ApiResponse[HistoryListResponse], summary="Get Paginated Analysis History")
async def get_history(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (LOW, MEDIUM, HIGH, CRITICAL)"),
    search: Optional[str] = Query(None, description="Search by product title or analysis ID"),
    sort_by: str = Query("created_at", description="Sort by field (created_at, business_risk_index)"),
    order: str = Query("desc", description="Sort order (asc, desc)"),
    current_user: User = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Retrieves user-scoped paginated historical risk analyses ordered by most recent first.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    analyses, total = service.get_history_paginated(
        user_id=current_user.id,
        page=page,
        limit=limit,
        risk_level=risk_level,
        search=search,
        sort_by=sort_by,
        order=order,
    )

    total_pages = math.ceil(total / limit) if total > 0 else 0

    items = [
        HistoryItemResponse(
            analysisId=item.public_id,
            productTitle=item.product.product_title if item.product else "Product",
            productUrl=item.product.product_url if item.product else "",
            sellerName=item.product.seller_name if item.product else "N/A",
            imageUrl=item.product.image_url if item.product else "",
            businessRiskIndex=item.business_risk_index,
            businessRiskLevel=item.business_risk_level,
            qualityRiskScore=item.quality_risk_score,
            deliveryRiskScore=item.delivery_risk_score,
            trustRiskScore=item.trust_risk_score,
            totalReviews=item.total_reviews,
            createdAt=item.created_at.isoformat() if item.created_at else "",
        )
        for item in analyses
    ]

    response_payload = HistoryListResponse(
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
        message="Analysis history retrieved successfully.",
        data=response_payload,
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION,
        ),
    )


@router.get("/{analysisId}", response_model=ApiResponse[AnalysisDetailResponse], summary="Get Complete Stored Analysis")
async def get_analysis_detail(
    request: Request,
    analysisId: str,
    current_user: User = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Retrieves complete stored analysis by public business identifier (anl_...).
    Scoped strictly to current user.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    analysis = service.get_analysis_by_public_id(analysisId, user_id=current_user.id)

    if not analysis:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "message": f"Analysis with ID '{analysisId}' was not found.",
                "data": None,
                "meta": {
                    "requestId": request_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "version": settings.APP_VERSION,
                },
            },
        )

    product_dict = {
        "id": str(analysis.product.id) if analysis.product else "",
        "title": analysis.product.product_title if analysis.product else "Product",
        "productTitle": analysis.product.product_title if analysis.product else "Product",
        "url": analysis.product.product_url if analysis.product else "",
        "productUrl": analysis.product.product_url if analysis.product else "",
        "platform": analysis.product.platform if analysis.product else "Daraz",
        "rating": analysis.product.overall_rating if analysis.product else 0.0,
        "overallRating": analysis.product.overall_rating if analysis.product else 0.0,
        "seller": analysis.product.seller_name if (analysis.product and analysis.product.seller_name) else "N/A",
        "sellerName": analysis.product.seller_name if (analysis.product and analysis.product.seller_name) else "N/A",
        "imageUrl": analysis.product.image_url if analysis.product else "",
        "image_url": analysis.product.image_url if analysis.product else "",
        "category": analysis.product.category if (analysis.product and analysis.product.category) else "N/A",
        "reviewCount": analysis.total_reviews,
        "totalReviews": analysis.total_reviews,
    }

    metrics_dict = {
        "totalReviews": analysis.total_reviews,
        "totalPositiveReviews": analysis.total_positive_reviews,
        "totalNegativeReviews": analysis.total_negative_reviews,
        "totalNeutralReviews": analysis.total_neutral_reviews,
        "averageConfidence": analysis.average_confidence,
    }

    risks_dict = {
        "qualityRiskScore": analysis.quality_risk_score,
        "deliveryRiskScore": analysis.delivery_risk_score,
        "trustRiskScore": analysis.trust_risk_score,
        "businessRiskIndex": analysis.business_risk_index,
        "businessRiskLevel": analysis.business_risk_level,
    }

    breakdowns_dict = {
        "aspectStatistics": analysis.aspect_statistics or {},
        "confidenceStatistics": analysis.confidence_statistics or {},
        "riskBreakdown": analysis.risk_breakdown or {},
    }

    raw_review_summaries = [
        ReviewSummaryResponse(
            id=str(r.id),
            reviewText=r.review_text,
            sentiment=str(r.sentiment or "NEUTRAL").upper(),
            confidenceScore=float(r.confidence_score or 0.85),
            aspects=r.aspects,
        )
        for r in (analysis.reviews or [])
        if r.review_text
    ]

    review_summaries = AnalysisMapper.extract_top_reviews_per_class(raw_review_summaries, max_per_class=10)

    rec_dict = AnalysisMapper.generate_recommendation_dict(
        quality_score=analysis.quality_risk_score,
        delivery_score=analysis.delivery_risk_score,
        trust_score=analysis.trust_risk_score,
        business_risk_index=analysis.business_risk_index,
        business_risk_level=analysis.business_risk_level,
    )

    detail_payload = AnalysisDetailResponse(
        analysisId=analysis.public_id,
        status=analysis.status,
        executionDurationMs=analysis.execution_duration_ms,
        createdAt=analysis.created_at.isoformat() if analysis.created_at else "",
        product=product_dict,
        metrics=metrics_dict,
        risks=risks_dict,
        recommendation=rec_dict,
        breakdowns=breakdowns_dict,
        reviews=review_summaries,
    )

    return ApiResponse(
        success=True,
        message="Analysis detail retrieved successfully.",
        data=detail_payload,
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION,
        ),
    )


@router.delete("/{analysisId}", response_model=ApiResponse[dict], summary="Delete Stored Analysis")
async def delete_analysis(
    request: Request,
    analysisId: str,
    current_user: User = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Deletes a stored analysis owned by current user.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    success = service.delete_analysis_by_public_id(analysisId, user_id=current_user.id)

    if not success:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "message": f"Analysis with ID '{analysisId}' not found or could not be deleted.",
                "data": None,
                "meta": {
                    "requestId": request_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "version": settings.APP_VERSION,
                },
            },
        )

    return ApiResponse(
        success=True,
        message=f"Analysis '{analysisId}' successfully deleted.",
        data={"deletedAnalysisId": analysisId},
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION,
        ),
    )

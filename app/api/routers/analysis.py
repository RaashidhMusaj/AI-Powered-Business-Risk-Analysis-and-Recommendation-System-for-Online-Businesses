from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from datetime import datetime, timezone

from app.api.schemas.common_schema import ApiResponse, ApiMeta
from app.api.schemas.analysis_schema import AnalysisRequest, AnalysisResultResponse
from app.api.schemas.demo_schema import (
    ProductCheckRequest,
    ProductPreviewResponse,
    AnalysisStartResponse,
    AnalysisStopRequest,
    AnalysisStatusResponse,
)

from app.services.analysis_service import AnalysisService
from app.mappers.analysis_mapper import AnalysisMapper
from app.api.dependencies.services import get_analysis_service
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.constants.api_constants import APIConstants
from app.constants.messages import APIMessages
from app.config.settings import settings

router = APIRouter(prefix="/v1/analysis", tags=[APIConstants.TAG_ANALYSIS])


@router.post("/check-product", response_model=ApiResponse[ProductPreviewResponse], summary="Step 1: Check Product Preview")
async def check_product(
    request: Request,
    body: ProductCheckRequest,
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Validates URL and extracts product preview information (Title, Image, Seller, Rating, Review Count, Platform, Category) via Selenium.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    preview = await service.check_product(body.productUrl)

    return ApiResponse(
        success=True,
        message="Product information extracted successfully.",
        data=ProductPreviewResponse(**preview),
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION,
        ),
    )


@router.post("/start", response_model=ApiResponse[AnalysisStartResponse], summary="Step 2: Start Guided Analysis Job")
async def start_analysis(
    request: Request,
    body: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Starts background review scraping and AI processing job bound to current authenticated user.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    save_history = body.options.saveHistory if body.options else True

    job_data = await service.start_analysis(
        product_url=body.productUrl,
        user_id=current_user.id,
        save_history=save_history,
    )

    return ApiResponse(
        success=True,
        message=job_data["message"],
        data=AnalysisStartResponse(
            analysisId=job_data["analysisId"],
            status=job_data["status"],
            message=job_data["message"],
        ),
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION,
        ),
    )


@router.post("/stop", response_model=ApiResponse[dict], summary="Step 3: Finish Scraping (Trigger Q Key)")
async def stop_scraping(
    request: Request,
    body: AnalysisStopRequest,
    current_user: User = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Triggers 'Finish Scraping' stop signal for job owned by current user.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    success = service.finish_scraping(body.analysisId, user_id=current_user.id)

    if not success:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": f"Job '{body.analysisId}' is not active or could not be stopped.",
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
        message="Finish Scraping requested. Scraper is stopping review collection and proceeding to AI processing...",
        data={"analysisId": body.analysisId, "stopRequested": True},
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION,
        ),
    )


@router.get("/status/{analysisId}", response_model=ApiResponse[AnalysisStatusResponse], summary="Step 4: Poll Job Status")
async def get_job_status(
    request: Request,
    analysisId: str,
    current_user: User = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Polled by frontend to display live progress for user job.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    status_data = service.get_status(analysisId, user_id=current_user.id)

    return ApiResponse(
        success=True,
        message="Job status retrieved.",
        data=AnalysisStatusResponse(**status_data),
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION,
        ),
    )


@router.get("/result/{analysisId}", response_model=ApiResponse[AnalysisResultResponse], summary="Step 5: Get Final Analysis Result")
async def get_job_result(
    request: Request,
    analysisId: str,
    current_user: User = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Retrieves final risk analysis result scoped to current user.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    stored = service.get_analysis_by_public_id(analysisId, user_id=current_user.id)

    if not stored:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "message": f"Result for analysis '{analysisId}' not found or still processing.",
                "data": None,
                "meta": {
                    "requestId": request_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "version": settings.APP_VERSION,
                },
            },
        )

    product_dict = {
        "title": stored.product.product_title if stored.product else "Product",
        "productTitle": stored.product.product_title if stored.product else "Product",
        "url": stored.product.product_url if stored.product else "",
        "productUrl": stored.product.product_url if stored.product else "",
        "reviewCount": stored.total_reviews,
        "totalReviews": stored.total_reviews,
        "rating": stored.product.overall_rating if stored.product else 0.0,
        "overallRating": stored.product.overall_rating if stored.product else 0.0,
        "seller": stored.product.seller_name if stored.product else "N/A",
        "sellerName": stored.product.seller_name if stored.product else "N/A",
        "imageUrl": stored.product.image_url if stored.product else "",
        "category": stored.product.category if stored.product else "N/A",
        "platform": stored.product.platform if stored.product else "Daraz",
    }

    pos_c = stored.total_positive_reviews
    neg_c = stored.total_negative_reviews
    neu_c = stored.total_neutral_reviews

    if (pos_c + neg_c + neu_c) == 0 and stored.reviews:
        for rev in stored.reviews:
            s_val = str(rev.sentiment or "").upper()
            if "POS" in s_val: pos_c += 1
            elif "NEG" in s_val: neg_c += 1
            elif "NEU" in s_val or "MIX" in s_val: neu_c += 1
            else: pos_c += 1

    statistics_dict = {
        "reviewStatistics": {
            "total_reviews": stored.total_reviews,
            "positive_reviews": pos_c,
            "negative_reviews": neg_c,
            "neutral_reviews": neu_c,
            "positive": pos_c,
            "negative": neg_c,
            "neutral": neu_c,
        },
        "sentimentStatistics": {
            "total_reviews": stored.total_reviews,
            "positive_reviews": pos_c,
            "negative_reviews": neg_c,
            "neutral_reviews": neu_c,
            "positive": pos_c,
            "negative": neg_c,
            "neutral": neu_c,
            "positive_ratio": round(pos_c / max(1, stored.total_reviews), 4),
            "negative_ratio": round(neg_c / max(1, stored.total_reviews), 4),
            "neutral_ratio": round(neu_c / max(1, stored.total_reviews), 4),
        },
        "aspectStatistics": stored.aspect_statistics or {},
        "confidenceStatistics": stored.confidence_statistics or {},
    }

    def get_level(score):
        score_val = float(score)
        if score_val < 20.0: return "VERY_LOW"
        if score_val < 40.0: return "LOW"
        if score_val < 60.0: return "MEDIUM"
        if score_val < 80.0: return "HIGH"
        return "CRITICAL"

    q_score = stored.quality_risk_score
    d_score = stored.delivery_risk_score
    t_score = stored.trust_risk_score

    rb = stored.risk_breakdown or {}
    q_level = (rb.get("qualityRisk") or {}).get("level") or get_level(q_score)
    d_level = (rb.get("deliveryRisk") or {}).get("level") or get_level(d_score)
    t_level = (rb.get("trustRisk") or {}).get("level") or get_level(t_score)

    risks_dict = {
        "qualityRisk": {"score": q_score, "level": q_level},
        "deliveryRisk": {"score": d_score, "level": d_level},
        "trustRisk": {"score": t_score, "level": t_level},
        "businessRiskIndex": stored.business_risk_index,
        "overallRiskLevel": stored.business_risk_level,
        "riskBreakdown": rb,
    }

    neg_texts = [
        r.review_text
        for r in (stored.reviews or [])
        if str(r.sentiment or "").lower() == "negative" and r.review_text
    ][:20]

    db_reviews_list = []
    for r in (stored.reviews or []):
        if r.review_text:
            s_val = str(r.sentiment or "NEUTRAL").upper()
            c_val = float(r.confidence_score or 0.85)
            asp_dict = r.aspects if isinstance(r.aspects, dict) else {}
            detected = asp_dict.get("detected", []) if isinstance(asp_dict, dict) else []
            asp_val = str(detected[0]).upper() if (detected and len(detected) > 0) else "GENERAL"
            db_reviews_list.append({
                "id": str(r.id),
                "reviewText": r.review_text,
                "sentiment": s_val,
                "confidenceScore": c_val,
                "aspect": asp_val,
            })

    top_reviews = AnalysisMapper.extract_top_reviews_per_class(db_reviews_list, max_per_class=10)

    rec_dict = AnalysisMapper.generate_recommendation_dict(
        quality_score=q_score,
        delivery_score=d_score,
        trust_score=t_score,
        business_risk_index=stored.business_risk_index,
        business_risk_level=stored.business_risk_level,
    )

    result_payload = {
        "analysisId": stored.public_id,
        "status": stored.status,
        "product": product_dict,
        "statistics": statistics_dict,
        "risks": risks_dict,
        "recommendation": rec_dict,
        "reviews": top_reviews,
        "negativeReviews": neg_texts,
    }

    return ApiResponse(
        success=True,
        message="Analysis result retrieved successfully.",
        data=AnalysisResultResponse(**result_payload),
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION,
        ),
    )


@router.post("", response_model=ApiResponse[AnalysisResultResponse], summary="Execute Direct Business Risk Analysis")
async def analyze_product(
    request: Request,
    body: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Direct synchronous endpoint executing end-to-end AI analysis pipeline for current user.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    save_history = body.options.saveHistory if body.options else True

    result_data = await service.analyze_product(
        product_url=body.productUrl,
        user_id=current_user.id,
        save_history=save_history
    )

    return ApiResponse(
        success=True,
        message=APIMessages.SUCCESS_ANALYSIS,
        data=AnalysisResultResponse(**result_data),
        meta=ApiMeta(
            requestId=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.APP_VERSION,
        ),
    )

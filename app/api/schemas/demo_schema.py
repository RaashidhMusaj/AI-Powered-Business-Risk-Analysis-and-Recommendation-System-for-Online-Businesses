from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class ProductCheckRequest(BaseModel):
    """
    Request model for validating and previewing product information.
    """
    productUrl: str = Field(..., description="Target Daraz e-commerce product URL")


class ProductPreviewResponse(BaseModel):
    """
    Response payload containing extracted product preview information.
    """
    productUrl: str = Field(..., description="Product URL")
    title: str = Field(..., description="Product Title")
    imageUrl: str = Field(..., description="Product main image URL")
    seller: str = Field(..., description="Seller or Store name")
    overallRating: float = Field(..., description="Overall rating score")
    totalReviews: int = Field(..., description="Total review count")
    platform: str = Field("Daraz", description="Platform name")
    category: Optional[str] = Field("General", description="Product category")


class AnalysisStartResponse(BaseModel):
    """
    Response payload returned upon starting a background analysis job.
    """
    analysisId: str = Field(..., description="Public analysis job identifier")
    status: str = Field(..., description="Current job status (e.g. SCRAPING)")
    message: str = Field(..., description="Status message")


class AnalysisStopRequest(BaseModel):
    """
    Request model for triggering 'Finish Scraping' stop signal.
    """
    analysisId: str = Field(..., description="Active analysis job identifier")


class AnalysisStatusResponse(BaseModel):
    """
    Real-time status response polled by the demo frontend.
    """
    analysisId: str = Field(..., description="Public analysis job identifier")
    status: str = Field(..., description="Current stage status (CHECKING, SCRAPING, AI_ANALYSIS, COMPLETED, FAILED)")
    currentStep: str = Field(..., description="Detailed step message")
    currentPage: int = Field(1, description="Current page being scraped")
    totalPages: int = Field(1, description="Total pages count")
    reviewsCollected: int = Field(0, description="Total reviews collected so far")
    progress: int = Field(0, description="Progress percentage (0-100)")
    elapsedTime: str = Field("00:00:00", description="Formatted elapsed duration")
    logs: List[str] = Field(default_factory=list, description="Timestamped progress log entries")

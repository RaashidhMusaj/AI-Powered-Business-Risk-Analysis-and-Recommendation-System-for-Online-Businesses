from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PaginationMeta(BaseModel):
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    totalItems: int = Field(..., description="Total matching items count")
    totalPages: int = Field(..., description="Total pages count")


class HistoryItemResponse(BaseModel):
    analysisId: str = Field(..., description="Public analysis business identifier")
    productTitle: str = Field(..., description="Product title")
    productUrl: str = Field(..., description="Product URL")
    sellerName: Optional[str] = Field(None, description="Seller or Store name")
    imageUrl: Optional[str] = Field(None, description="Product image URL")
    businessRiskIndex: float = Field(..., description="Overall business risk index")
    businessRiskLevel: str = Field(..., description="Business risk level category")
    qualityRiskScore: float = Field(..., description="Quality FIS risk score")
    deliveryRiskScore: float = Field(..., description="Delivery FIS risk score")
    trustRiskScore: float = Field(..., description="Trust FIS risk score")
    totalReviews: int = Field(..., description="Total reviews analyzed")
    createdAt: str = Field(..., description="Analysis timestamp")


class HistoryListResponse(BaseModel):
    items: List[HistoryItemResponse] = Field(..., description="List of historical analysis summaries")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")


class ReviewSummaryResponse(BaseModel):
    id: str = Field(..., description="Review ID")
    reviewText: str = Field(..., description="Original review text")
    sentiment: Optional[str] = Field(None, description="Detected sentiment")
    confidenceScore: float = Field(..., description="Model confidence score")
    aspects: Optional[Dict[str, Any]] = Field(None, description="Aspect probabilities & detected aspects")


class AnalysisDetailResponse(BaseModel):
    analysisId: str = Field(..., description="Public analysis business identifier")
    status: str = Field(..., description="Execution status")
    executionDurationMs: float = Field(..., description="Execution duration in milliseconds")
    createdAt: str = Field(..., description="Creation timestamp")
    product: Dict[str, Any] = Field(..., description="Associated product details")
    metrics: Dict[str, Any] = Field(..., description="First-class review & confidence metrics")
    risks: Dict[str, Any] = Field(..., description="Fuzzy risk scores and business risk index")
    recommendation: Optional[Dict[str, Any]] = Field(None, description="Actionable recommendation report")
    breakdowns: Dict[str, Any] = Field(..., description="Aspect statistics and risk breakdown")
    reviews: List[ReviewSummaryResponse] = Field(default_factory=list, description="Sample of processed reviews")


class ProductItemResponse(BaseModel):
    id: str = Field(..., description="Product internal ID")
    productUrl: str = Field(..., description="Product URL")
    productTitle: str = Field(..., description="Product title")
    platform: str = Field(..., description="Platform name")
    category: Optional[str] = Field(None, description="Category")
    overallRating: float = Field(..., description="Overall rating")
    totalReviews: int = Field(..., description="Total reviews count")
    sellerName: Optional[str] = Field(None, description="Seller or Store name")
    imageUrl: Optional[str] = Field(None, description="Product image URL")
    createdAt: str = Field(..., description="Creation timestamp")


class ProductListResponse(BaseModel):
    items: List[ProductItemResponse] = Field(..., description="List of analyzed products")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")

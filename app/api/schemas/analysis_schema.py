from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class AnalysisOptions(BaseModel):
    """
    Optional analysis configuration options.
    """
    saveHistory: bool = Field(True, description="Save analysis to database history")


class AnalysisRequest(BaseModel):
    """
    Request model for product risk analysis.
    """
    productUrl: str = Field(..., description="Target e-commerce product URL (e.g. Daraz product page)")
    options: Optional[AnalysisOptions] = Field(default_factory=AnalysisOptions, description="Analysis execution options")


class ProductInfoSchema(BaseModel):
    title: Optional[str] = Field(None, description="Product title")
    productTitle: Optional[str] = Field(None, description="Product title alternative")
    url: Optional[str] = Field(None, description="Product URL")
    productUrl: Optional[str] = Field(None, description="Product URL alternative")
    reviewCount: Optional[int] = Field(0, description="Total scraped reviews count")
    totalReviews: Optional[int] = Field(0, description="Total scraped reviews count alternative")
    rating: Optional[float] = Field(0.0, description="Average rating")
    overallRating: Optional[float] = Field(0.0, description="Average rating alternative")
    seller: Optional[str] = Field(None, description="Seller name")
    sellerName: Optional[str] = Field(None, description="Seller name alternative")
    imageUrl: Optional[str] = Field(None, description="Product image URL")
    image_url: Optional[str] = Field(None, description="Product image URL alternative")
    category: Optional[str] = Field(None, description="Product category")
    platform: Optional[str] = Field("Daraz", description="Target platform")


class RiskScoreSchema(BaseModel):
    score: float = Field(..., description="Evaluated risk score (0-100)")
    level: str = Field(..., description="Risk level (LOW, MEDIUM, HIGH, CRITICAL)")


class RisksSchema(BaseModel):
    qualityRisk: RiskScoreSchema = Field(..., description="Quality FIS evaluation risk score")
    deliveryRisk: RiskScoreSchema = Field(..., description="Delivery FIS evaluation risk score")
    trustRisk: RiskScoreSchema = Field(..., description="Trust FIS evaluation risk score")
    businessRiskIndex: float = Field(..., description="Overall aggregated business risk index (0-100)")
    overallRiskLevel: str = Field(..., description="Overall business risk level category")
    riskBreakdown: Dict[str, Any] = Field(default_factory=dict, description="Detailed risk breakdown")


class RecommendationReportSchema(BaseModel):
    summary: str = Field("", description="Executive summary of recommendation report")
    insights: List[str] = Field(default_factory=list, description="Key risk insights identified")
    actions: List[str] = Field(default_factory=list, description="Prioritized mitigation actions")


class RecommendationMetadataSchema(BaseModel):
    highestPriority: str = Field("", description="Highest priority category")
    recommendationCount: int = Field(0, description="Total recommendation count")
    generatedAt: str = Field("", description="ISO timestamp of generation")


class RecommendationResultSchema(BaseModel):
    report: RecommendationReportSchema = Field(..., description="Report sections payload")
    metadata: RecommendationMetadataSchema = Field(..., description="Execution metadata")
    generatedTimestamp: str = Field("", description="Preserved UTC generation timestamp")
    version: str = Field("v1", description="Recommendation API version")
    processingTimeMs: int = Field(0, description="Processing duration in milliseconds")


class AnalysisResultResponse(BaseModel):
    """
    Full structured analysis result schema.
    """
    analysisId: str = Field(..., description="Unique analysis execution identifier")
    status: str = Field(..., description="Analysis completion status")
    product: ProductInfoSchema = Field(..., description="Product information")
    statistics: Dict[str, Any] = Field(..., description="Statistical, aspect, sentiment & confidence stats")
    risks: RisksSchema = Field(..., description="Fuzzy inference risks and overall business risk")
    recommendation: Optional[RecommendationResultSchema] = Field(None, description="Actionable recommendation outcome")
    negativeReviews: Optional[list[str]] = Field(default_factory=list, description="List of at most 20 negative customer review texts")

from dataclasses import dataclass
from typing import Any, Optional

from core.scraper.dto.product import Product
from core.business_risk.aggregation.aggregation_result import AggregationResult


@dataclass
class ProductAnalysisResult:
    """
    Represents the complete analysis result for a single product.

    This DTO is gradually populated as the product passes through
    each stage of the analysis pipeline.
    """

    product: Product
    aggregation_result: AggregationResult
    predictions: Optional[Any] = None

    # These will be populated in later phases
    business_risk: Optional[Any] = None
    reliability: Optional[Any] = None
    recommendations: Optional[Any] = None

    def to_dict(self) -> dict:
        """
        Convert the complete analysis result into a dictionary.
        """

        return {
            "product": self.product.__dict__,
            "aggregation_result": self.aggregation_result.to_dict(),
            "business_risk": self.business_risk,
            "reliability": self.reliability,
            "recommendations": self.recommendations,
        }

    def __str__(self) -> str:
        return (
            f"ProductAnalysisResult("
            f"product='{self.product.name}', "
            f"business_risk={self.business_risk})"
        )
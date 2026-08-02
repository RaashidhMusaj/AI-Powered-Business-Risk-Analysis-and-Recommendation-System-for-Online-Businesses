from typing import Dict, Any, Optional
from core.analysis.engine.product_analysis_engine import ProductAnalysisEngine
from core.scraper.engines.scraper_engine import ScraperEngine
from core.business_risk.prediction.prediction_collector import PredictionCollector
from core.business_risk.calculator.business_risk_calculator import BusinessRiskCalculator
from core.business_risk.fuzzy.quality_fis import QualityFIS
from core.business_risk.fuzzy.delivery_fis import DeliveryFIS
from core.business_risk.fuzzy.trust_fis import TrustFIS

from core.recommendation.service import RecommendationService
from core.models.analysis_result import AnalysisResult

from app.utils.logger import ai_logger, scraper_logger
from app.utils.exceptions import ScrapingFailedError, AIInferenceFailedError, AggregationFailedError
from app.state.core_state import app_state


class AIEngineAdapter:
    """
    Adapter isolating FastAPI services from internal core AI & FIS engines with thread isolation.
    """

    def __init__(
        self,
        engine: Optional[ProductAnalysisEngine] = None,
        recommendation_service: Optional[RecommendationService] = None,
    ):
        self._engine = engine or app_state.engine_instance or ProductAnalysisEngine()
        self._quality_fis = QualityFIS()
        self._delivery_fis = DeliveryFIS()
        self._trust_fis = TrustFIS()
        self._risk_calculator = BusinessRiskCalculator()
        self._recommendation_service = recommendation_service or RecommendationService()

    def extract_product_preview(self, product_url: str) -> Dict[str, Any]:
        """
        Extracts product preview metadata without executing full scraping or AI inference using an isolated scraper.
        """
        ai_logger.info(f"Extracting product preview via adapter: {product_url}")
        scraper = ScraperEngine()
        return scraper.extract_product_preview(product_url)

    def run_full_pipeline(self, product_url: str, job_state=None) -> Dict[str, Any]:
        """
        Executes end-to-end AI analysis pipeline synchronously with thread isolation.
        """
        ai_logger.info(f"Starting AI pipeline execution for URL: {product_url}")

        try:
            analysis_result = self._engine.analyze(product_url, job_state=job_state)
        except Exception as e:
            scraper_logger.error(f"Scraper / AI Pipeline error during analyze: {str(e)}")
            raise ScrapingFailedError(details={"url": product_url, "error": str(e)})

        if not analysis_result or not hasattr(analysis_result, "aggregation_result"):
            raise AIInferenceFailedError(details={"reason": "Null or invalid result from ProductAnalysisEngine"})

        aggregation = analysis_result.aggregation_result
        product = analysis_result.product
        stats = getattr(aggregation, "aspect_statistics", {})

        try:
            quality_eval = self._quality_fis.evaluate(
                mention_ratio=stats["quality"]["mention_ratio"],
                average_negative_strength=stats["quality"]["average_negative_strength"],
            )
            delivery_eval = self._delivery_fis.evaluate(
                mention_ratio=stats["delivery"]["mention_ratio"],
                average_negative_strength=stats["delivery"]["average_negative_strength"],
            )
            trust_eval = self._trust_fis.evaluate(
                mention_ratio=stats["trust"]["mention_ratio"],
                average_negative_strength=stats["trust"]["average_negative_strength"],
            )
        except Exception as e:
            ai_logger.error(f"Fuzzy Inference System evaluation failed: {str(e)}")
            raise AIInferenceFailedError(details={"reason": f"FIS evaluation error: {str(e)}"})

        try:
            business_risk = self._risk_calculator.calculate(
                aggregation=aggregation,
                quality=quality_eval,
                delivery=delivery_eval,
                trust=trust_eval,
            )
        except Exception as e:
            ai_logger.error(f"Business risk calculation failed: {str(e)}")
            raise AggregationFailedError(details={"reason": f"Risk calculator error: {str(e)}"})

        # Integration: Recommendation Pipeline via RecommendationService
        try:
            recommendation = self._recommendation_service.generate_recommendation(business_risk)
        except Exception as e:
            ai_logger.error(f"Recommendation generation failed in adapter: {str(e)}")
            raise

        unified_result = AnalysisResult(
            business_risk=business_risk,
            recommendation=recommendation,
        )

        ai_logger.info("Successfully executed complete AI risk and recommendation pipeline.")

        return {
            "product": product,
            "predictions": getattr(analysis_result, "predictions", []),
            "aggregation": aggregation,
            "quality": quality_eval,
            "delivery": delivery_eval,
            "trust": trust_eval,
            "business": business_risk,
            "recommendation": recommendation,
            "analysis_result": unified_result,
        }

    def scrape_product(self, product_url: str, job_state=None):
        """Scrapes product metadata and reviews using a thread-isolated ScraperEngine."""
        scraper = ScraperEngine()
        if job_state:
            scraper.job_state = job_state
        return scraper.scrape_product(product_url)

    def evaluate_predictions_and_risks(self, scraped_reviews: list) -> dict:
        """Runs predictions on reviews and evaluates Fuzzy Risk systems using a local collector."""
        predictions = self._engine._pipeline.predict_reviews(scraped_reviews)

        local_collector = PredictionCollector()
        local_collector.add_many(predictions)
        aggregation = self._engine._aggregator.aggregate(local_collector.get_all())

        stats = getattr(aggregation, "aspect_statistics", {})
        quality_eval = self._quality_fis.evaluate(
            mention_ratio=stats["quality"]["mention_ratio"],
            average_negative_strength=stats["quality"]["average_negative_strength"],
        )
        delivery_eval = self._delivery_fis.evaluate(
            mention_ratio=stats["delivery"]["mention_ratio"],
            average_negative_strength=stats["delivery"]["average_negative_strength"],
        )
        trust_eval = self._trust_fis.evaluate(
            mention_ratio=stats["trust"]["mention_ratio"],
            average_negative_strength=stats["trust"]["average_negative_strength"],
        )

        business_risk = self._risk_calculator.calculate(
            aggregation=aggregation,
            quality=quality_eval,
            delivery=delivery_eval,
            trust=trust_eval,
        )

        recommendation = self._recommendation_service.generate_recommendation(business_risk)

        unified_result = AnalysisResult(
            business_risk=business_risk,
            recommendation=recommendation,
        )

        return {
            "predictions": predictions,
            "aggregation": aggregation,
            "quality": quality_eval,
            "delivery": delivery_eval,
            "trust": trust_eval,
            "business": business_risk,
            "recommendation": recommendation,
            "analysis_result": unified_result,
        }

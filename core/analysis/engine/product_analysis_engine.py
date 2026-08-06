from core.analysis.dto.product_analysis_result import ProductAnalysisResult
from core.scraper.engines.scraper_engine import ScraperEngine
from core.ai.pipeline import ReviewPredictionPipeline
from core.business_risk.prediction.prediction_collector import PredictionCollector
from core.scraper.dto.product import Product
from core.business_risk.aggregation.statistical_aggregator import StatisticalAggregator


class ProductAnalysisEngine:
    """
    Coordinates the product analysis workflow with thread-isolated execution context.
    """

    def __init__(self):
        self._pipeline = ReviewPredictionPipeline()
        self._aggregator = StatisticalAggregator()

    def get_scraper(self) -> ScraperEngine:
        """Returns a new, request-isolated ScraperEngine instance."""
        return ScraperEngine()

    def analyze(self, product_url: str, job_state=None):
        scraper = self.get_scraper()
        if job_state:
            scraper.job_state = job_state

        product = scraper.scrape_product(product_url)
        predictions = self._pipeline.predict_reviews(product.reviews)

        # Thread-isolated PredictionCollector per invocation
        local_collector = PredictionCollector()
        local_collector.add_many(predictions)

        aggregation_result = self._aggregator.aggregate(local_collector.get_all())

        return ProductAnalysisResult(
            product=product,
            aggregation_result=aggregation_result,
            predictions=predictions
        )
import asyncio
import time
import uuid
from typing import Dict, Any, Optional, Tuple, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.adapters.ai_engine_adapter import AIEngineAdapter
from app.mappers.analysis_mapper import AnalysisMapper, sanitize_native_types
from app.repositories.product_repository import ProductRepository
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.review_repository import ReviewRepository
from app.state.job_state import job_state_manager, JobState

from app.models.product import Product
from app.models.analysis import Analysis
from app.models.review import Review

from app.utils.exceptions import InvalidProductURLError, InternalServerError
from app.utils.logger import api_logger, db_logger
from app.domain.enums import AnalysisStatus


class AnalysisService:
    """
    Business Service orchestrating AI analysis pipeline, guided job execution, and tenant-isolated persistence.
    """

    def __init__(
        self,
        db: Optional[Session] = None,
        adapter: Optional[AIEngineAdapter] = None,
        product_repo: Optional[ProductRepository] = None,
        analysis_repo: Optional[AnalysisRepository] = None,
        review_repo: Optional[ReviewRepository] = None,
    ):
        self.db = db
        self.adapter = adapter or AIEngineAdapter()
        self.product_repo = product_repo or (ProductRepository(db) if db else None)
        self.analysis_repo = analysis_repo or (AnalysisRepository(db) if db else None)
        self.review_repo = review_repo or (ReviewRepository(db) if db else None)

    def _validate_url(self, url: str):
        if not url or not isinstance(url, str) or not url.startswith("http"):
            raise InvalidProductURLError(
                details={"provided_url": url, "reason": "URL must start with http:// or https://"}
            )

    async def check_product(self, product_url: str) -> Dict[str, Any]:
        """
        Step 1: Validates product URL and extracts product preview metadata via Selenium.
        """
        self._validate_url(product_url)
        api_logger.info(f"Checking product preview for URL: {product_url}")

        preview_data = await asyncio.to_thread(
            self.adapter.extract_product_preview, product_url
        )
        return preview_data

    async def start_analysis(self, product_url: str, user_id: UUID, save_history: bool = True) -> Dict[str, Any]:
        """
        Step 2: Starts background analysis job bound to tenant user_id.
        """
        self._validate_url(product_url)
        job = job_state_manager.create_job(product_url, user_id=str(user_id))
        job.status = "SCRAPING"
        job.current_step = "Connecting to product page..."
        job.progress_percent = 10

        api_logger.info(f"Started guided background analysis job [{job.analysis_id}] for user [{user_id}]")

        # Launch async execution loop in background
        asyncio.create_task(self._run_async_job(job, user_id, save_history))

        return {
            "analysisId": job.analysis_id,
            "status": "SCRAPING",
            "message": "Analysis job started successfully. Scraping in progress..."
        }

    def finish_scraping(self, analysis_id: str, user_id: Optional[UUID] = None) -> bool:
        """
        Step 3: Triggers 'Finish Scraping' stop signal (replicating keyboard key 'Q').
        """
        api_logger.info(f"Received 'Finish Scraping' request for job [{analysis_id}] (User: {user_id})")
        return job_state_manager.request_stop(analysis_id, user_id=str(user_id) if user_id else None)

    def get_status(self, analysis_id: str, user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Step 4: Returns real-time job status polled by frontend.
        """
        job = job_state_manager.get_job(analysis_id, user_id=str(user_id) if user_id else None)
        if not job:
            # Fallback query from DB if job is not active in memory
            stored = self.get_analysis_by_public_id(analysis_id, user_id=user_id)
            if stored:
                return {
                    "analysisId": analysis_id,
                    "status": stored.status,
                    "currentStep": "Analysis Completed",
                    "currentPage": 1,
                    "totalPages": 1,
                    "reviewsCollected": stored.total_reviews,
                    "progress": 100,
                    "elapsedTime": "00:00:00"
                }
            return {
                "analysisId": analysis_id,
                "status": "UNKNOWN",
                "currentStep": "Job not found",
                "currentPage": 0,
                "totalPages": 0,
                "reviewsCollected": 0,
                "progress": 0,
                "elapsedTime": "00:00:00"
            }

        return {
            "analysisId": job.analysis_id,
            "status": job.status,
            "currentStep": job.current_step,
            "currentPage": job.current_page,
            "totalPages": job.total_pages,
            "reviewsCollected": job.reviews_collected,
            "progress": job.progress_percent,
            "elapsedTime": job.get_elapsed_time_str(),
            "logs": list(job.log_entries)
        }

    async def _run_async_job(self, job: JobState, user_id: UUID, save_history: bool):
        """
        Internal worker running scraper and full AI pipeline in background.
        """
        try:
            job.current_step = "Scraping reviews from product page..."
            job.progress_percent = 15
            job.add_log("SCRAPER", "Connecting to Daraz product page via Selenium...")

            # Phase 1: Web Scraping & Immediate DB Staging
            raw_product = await asyncio.to_thread(
                self.adapter.scrape_product, job.product_url, job
            )

            job.current_step = "Staging scraped reviews into PostgreSQL..."
            job.progress_percent = 45
            job.add_log("DATABASE", f"Committing {len(getattr(raw_product, 'reviews', []))} raw reviews to PostgreSQL...")

            staged_info = {}
            if save_history:
                try:
                    with SessionLocal() as db_session:
                        staged_info = self._stage_scraped_data(db_session, job.analysis_id, job.product_url, raw_product, user_id, job)
                except Exception as db_err:
                    api_logger.error(f"Database staging error during job [{job.analysis_id}]: {db_err}", exc_info=True)
                    job.add_log("ERROR", f"Database staging warning: {db_err}")

            # Phase 2: AI Predictions & Fuzzy Logic Evaluation
            job.status = "AI_ANALYSIS"
            job.current_step = "Running XLM-R + Adapter AI Inference on Staged Reviews..."
            job.progress_percent = 65
            job.add_log("AI_ENGINE", "Preprocessing & tokenizing multilingual review texts...")
            job.add_log("AI_ENGINE", "Running XLM-R backbone + adapter classification head...")
            job.add_log("FIS", "Evaluating Quality, Delivery, and Trust Fuzzy Inference Systems...")

            scraped_reviews = getattr(raw_product, "reviews", [])
            eval_output = await asyncio.to_thread(
                self.adapter.evaluate_predictions_and_risks, scraped_reviews
            )

            pipeline_output = {
                "product": raw_product,
                **eval_output
            }
            mapped_data = AnalysisMapper.to_api_result(pipeline_output)

            # Phase 3: Finalize Analysis Risk Scores in PostgreSQL
            if save_history and staged_info.get("analysis_db_id"):
                job.current_step = "Finalizing Analysis Risk Scores in PostgreSQL..."
                job.progress_percent = 90
                job.add_log("DATABASE", "Updating Analysis risk scores and Review AI predictions in PostgreSQL...")
                try:
                    with SessionLocal() as db_session:
                        self._finalize_staged_analysis(db_session, staged_info["analysis_db_id"], mapped_data, eval_output, job)
                except Exception as db_err:
                    api_logger.error(f"Database finalization error during job [{job.analysis_id}]: {db_err}", exc_info=True)
                    job.add_log("ERROR", f"Database finalization warning: {db_err}")

            job.status = AnalysisStatus.COMPLETED.value
            job.end_time = time.time()
            job.current_step = "Analysis Completed"
            job.progress_percent = 100
            job.add_log("COMPLETED", f"Business Risk Analysis [{job.analysis_id}] finished successfully.")
            job.result = {
                "analysisId": job.analysis_id,
                "status": AnalysisStatus.COMPLETED.value,
                "product": mapped_data["product"],
                "statistics": mapped_data["statistics"],
                "risks": mapped_data["risks"],
                "recommendation": mapped_data.get("recommendation"),
                "reviews": mapped_data.get("reviews", []),
            }
            api_logger.info(f"Background job [{job.analysis_id}] completed successfully.")

        except Exception as e:
            job.status = AnalysisStatus.FAILED.value
            job.end_time = time.time()
            job.current_step = f"Analysis Failed: {str(e)}"
            job.error_message = str(e)
            job.add_log("ERROR", f"Job execution failed: {str(e)}")
            api_logger.error(f"Background job [{job.analysis_id}] failed: {str(e)}", exc_info=True)

    def _stage_scraped_data(self, db: Session, analysis_id: str, product_url: str, raw_product: Any, user_id: UUID, job: JobState) -> dict:
        product_repo = ProductRepository(db=db)
        analysis_repo = AnalysisRepository(db=db)
        review_repo = ReviewRepository(db=db)

        title_val = str(getattr(raw_product, "product_title", "") or getattr(raw_product, "name", "") or "Daraz Product")[:500]
        seller_val = str(getattr(raw_product, "seller_name", "") or getattr(raw_product, "seller", "") or "Daraz Verified Seller")[:250]
        img_val = str(getattr(raw_product, "image_url", "") or "")[:2000]
        cat_val = str(getattr(raw_product, "category", "") or "Electronics")[:500]
        platform_val = str(getattr(raw_product, "platform", "") or "Daraz")[:60]
        rating_val = float(getattr(raw_product, "overall_rating", 0.0) or getattr(raw_product, "rating", 0.0))
        scraped_reviews = getattr(raw_product, "reviews", [])
        reviews_val = len(scraped_reviews)

        existing_product = product_repo.get_by_url(product_url, user_id=user_id)
        if not existing_product:
            try:
                existing_product = Product(
                    user_id=user_id,
                    product_url=product_url,
                    product_title=title_val,
                    platform=platform_val,
                    category=cat_val,
                    overall_rating=rating_val,
                    total_reviews=reviews_val,
                    seller_name=seller_val,
                    image_url=img_val
                )
                product_repo.add(existing_product)
                db.flush()
            except Exception:
                db.rollback()
                existing_product = product_repo.get_by_url(product_url)
        else:
            existing_product.product_title = title_val
            existing_product.platform = platform_val
            existing_product.category = cat_val
            existing_product.overall_rating = rating_val
            existing_product.total_reviews = reviews_val
            existing_product.seller_name = seller_val
            existing_product.image_url = img_val
            db.flush()

        analysis_entity = Analysis(
            public_id=analysis_id,
            user_id=user_id,
            product_id=existing_product.id,
            status=AnalysisStatus.SCRAPED.value,
            execution_duration_ms=0.0,
            quality_risk_score=0.0,
            delivery_risk_score=0.0,
            trust_risk_score=0.0,
            business_risk_index=0.0,
            business_risk_level="PENDING",
            total_reviews=reviews_val,
            total_positive_reviews=0,
            total_negative_reviews=0,
            total_neutral_reviews=0,
            average_confidence=0.0,
        )
        analysis_repo.add(analysis_entity)
        db.flush()

        review_entities = []
        for rev in scraped_reviews:
            rev_text = getattr(rev, "review_text", "")
            if rev_text:
                review_entities.append(
                    Review(
                        user_id=user_id,
                        analysis_id=analysis_entity.id,
                        review_text=rev_text,
                        sentiment=None,
                        confidence_score=0.0,
                        aspects=None
                    )
                )

        if review_entities:
            review_repo.bulk_add(review_entities)

        db.commit()
        db_logger.info(f"Staged {len(review_entities)} raw reviews for analysis [{analysis_id}] for user [{user_id}] into DB successfully.")
        return {"product_id": existing_product.id, "analysis_db_id": analysis_entity.id}

    def _finalize_staged_analysis(self, db: Session, analysis_db_id: Any, mapped_data: dict, eval_output: dict, job: JobState):
        analysis = db.query(Analysis).filter(Analysis.id == analysis_db_id).first()
        if not analysis:
            return

        stats_info = mapped_data["statistics"]
        risks_info = mapped_data["risks"]
        rev_stats = stats_info.get("reviewStatistics", {}) or stats_info.get("sentimentStatistics", {})
        sent_stats = stats_info.get("sentimentStatistics", {})
        pos_count = int(rev_stats.get("positive_reviews", rev_stats.get("positive", sent_stats.get("positive", 0))))
        neg_count = int(rev_stats.get("negative_reviews", rev_stats.get("negative", sent_stats.get("negative", 0))))
        neu_count = int(rev_stats.get("neutral_reviews", rev_stats.get("neutral", sent_stats.get("neutral", 0))))

        conf_stats = stats_info.get("confidenceStatistics", {})
        avg_conf = float(conf_stats.get("average_confidence", 0.0))
        execution_duration = float(round((time.time() - job.start_time) * 1000, 2))

        analysis.status = AnalysisStatus.COMPLETED.value
        analysis.execution_duration_ms = execution_duration
        analysis.quality_risk_score = float(risks_info["qualityRisk"]["score"])
        analysis.delivery_risk_score = float(risks_info["deliveryRisk"]["score"])
        analysis.trust_risk_score = float(risks_info["trustRisk"]["score"])
        analysis.business_risk_index = float(risks_info["businessRiskIndex"])
        analysis.business_risk_level = str(risks_info["overallRiskLevel"])
        analysis.total_positive_reviews = pos_count
        analysis.total_negative_reviews = neg_count
        analysis.total_neutral_reviews = neu_count
        analysis.average_confidence = avg_conf
        analysis.aspect_statistics = sanitize_native_types(stats_info.get("aspectStatistics"))
        analysis.confidence_statistics = sanitize_native_types(conf_stats)
        analysis.risk_breakdown = sanitize_native_types(risks_info.get("riskBreakdown"))

        # Update per-review AI predictions
        predictions = eval_output.get("predictions", [])
        reviews = db.query(Review).filter(Review.analysis_id == analysis.id).all()
        for i, r in enumerate(reviews):
            pred = predictions[i] if i < len(predictions) else {}
            r.sentiment = pred.get("sentiment")
            r.confidence_score = float(pred.get("confidence") or pred.get("confidence_score") or avg_conf)
            aspect_probs = pred.get("aspect_probabilities", {})
            detected_asps = pred.get("detected_aspects", [])
            r.aspects = sanitize_native_types({
                "quality": float(aspect_probs.get("quality", 0.0)),
                "delivery": float(aspect_probs.get("delivery", 0.0)),
                "trust": float(aspect_probs.get("trust", 0.0)),
                "detected": detected_asps
            })

        db.commit()
        db_logger.info(f"Finalized analysis [{analysis.public_id}] in DB successfully.")

    def resume_scraped_jobs(self):
        """Scans PostgreSQL on startup for uncompleted SCRAPED jobs and resumes AI prediction."""
        try:
            with SessionLocal() as db:
                unfinished = db.query(Analysis).filter(Analysis.status.in_([AnalysisStatus.SCRAPED.value, AnalysisStatus.PROCESSING.value])).all()
                if unfinished:
                    db_logger.info(f"Found {len(unfinished)} uncompleted SCRAPED jobs in DB on startup. Resuming AI prediction...")
                    for anl in unfinished:
                        reviews = db.query(Review).filter(Review.analysis_id == anl.id).all()
                        if reviews:
                            class DummyRev:
                                def __init__(self, t): self.review_text = t
                            scraped_revs = [DummyRev(r.review_text) for r in reviews]
                            eval_output = self.adapter.evaluate_predictions_and_risks(scraped_revs)
                            predictions = eval_output.get("predictions", [])

                            for i, r in enumerate(reviews):
                                pred = predictions[i] if i < len(predictions) else {}
                                r.sentiment = pred.get("sentiment")
                                r.confidence_score = float(pred.get("confidence", 0.0))
                                aspect_probs = pred.get("aspect_probabilities", {})
                                detected_asps = pred.get("detected_aspects", [])
                                r.aspects = sanitize_native_types({
                                    "quality": float(aspect_probs.get("quality", 0.0)),
                                    "delivery": float(aspect_probs.get("delivery", 0.0)),
                                    "trust": float(aspect_probs.get("trust", 0.0)),
                                    "detected": detected_asps
                                })

                            risks_info = eval_output.get("business", {})
                            anl.status = AnalysisStatus.COMPLETED.value
                            anl.quality_risk_score = float(eval_output["quality"].get("score", 0.0))
                            anl.delivery_risk_score = float(eval_output["delivery"].get("score", 0.0))
                            anl.trust_risk_score = float(eval_output["trust"].get("score", 0.0))
                            anl.business_risk_index = float(getattr(risks_info, "business_risk_index", 0.0) or 0.0)
                            anl.business_risk_level = str(getattr(risks_info, "overall_risk_level", "MEDIUM"))
                            db.commit()
                            db_logger.info(f"Resumed and finalized uncompleted job [{anl.public_id}] on startup successfully.")
        except Exception as err:
            db_logger.error(f"Error resuming uncompleted jobs on startup: {err}")
            raise

    async def analyze_product(self, product_url: str, user_id: UUID, save_history: bool = True) -> Dict[str, Any]:
        """
        Executes end-to-end direct analysis scoped to user_id.
        """
        self._validate_url(product_url)
        analysis_id = f"anl_{uuid.uuid4().hex[:12]}"
        start_time = time.time()

        api_logger.info(f"Received direct analysis request [{analysis_id}] for URL: {product_url} (User: {user_id})")

        pipeline_output = await asyncio.to_thread(
            self.adapter.run_full_pipeline, product_url
        )

        mapped_data = AnalysisMapper.to_api_result(pipeline_output)

        if save_history:
            dummy_job = JobState(analysis_id=analysis_id, product_url=product_url, user_id=str(user_id), start_time=start_time)
            with SessionLocal() as db_session:
                self._stage_scraped_data(db_session, analysis_id, product_url, pipeline_output["product"], user_id, dummy_job)
                self._finalize_staged_analysis(db_session, analysis_id, mapped_data, pipeline_output, dummy_job)

        return {
            "analysisId": analysis_id,
            "status": AnalysisStatus.COMPLETED.value,
            "product": mapped_data["product"],
            "statistics": mapped_data["statistics"],
            "risks": mapped_data["risks"],
            "recommendation": mapped_data.get("recommendation"),
            "reviews": mapped_data.get("reviews", []),
        }

    def get_history_paginated(
        self, user_id: UUID, page: int = 1, limit: int = 10, risk_level: Optional[str] = None, search: Optional[str] = None, sort_by: str = "created_at", order: str = "desc"
    ) -> Tuple[List[Analysis], int]:
        if not self.analysis_repo:
            return [], 0
        return self.analysis_repo.list_paginated(
            user_id=user_id, page=page, limit=limit, risk_level=risk_level, search=search, sort_by=sort_by, order=order
        )

    def get_analysis_by_public_id(self, public_id: str, user_id: Optional[UUID] = None) -> Optional[Analysis]:
        if not self.analysis_repo:
            return None
        return self.analysis_repo.get_by_public_id(public_id, user_id=user_id)

    def delete_analysis_by_public_id(self, public_id: str, user_id: UUID) -> bool:
        if not self.analysis_repo or not self.db:
            return False
        try:
            success = self.analysis_repo.delete_by_public_id(public_id, user_id=user_id)
            if success:
                self.db.commit()
            return success
        except Exception as e:
            self.db.rollback()
            db_logger.error(f"Failed to delete analysis [{public_id}] for user [{user_id}]: {str(e)}")
            raise InternalServerError(message=f"Failed to delete analysis record: {str(e)}")

    def get_products_paginated(self, user_id: UUID, page: int = 1, limit: int = 10) -> Tuple[List[Product], int]:
        if not self.product_repo:
            return [], 0
        return self.product_repo.list_paginated(user_id=user_id, page=page, limit=limit)

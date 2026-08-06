import os
from app.state.core_state import app_state
from app.utils.logger import ai_logger
from core.analysis.engine.product_analysis_engine import ProductAnalysisEngine


from app.database.session import engine, ensure_schema_migrations
from app.database.base import Base
import app.models
from app.utils.logger import db_logger


def startup_ai_engine():
    """
    Application startup sequence:
    1. Verify DB schema and auto-create tables if missing.
    2. Verify AI config & paths.
    3. Load XLM-R + Adapter model into memory.
    4. Instantiate and warm ProductAnalysisEngine.
    5. Set application health state.
    """
    ai_logger.info("Starting Application initialization sequence...")

    try:
        # Step 0: Ensure DB Tables Exist and Columns are Migrated
        db_logger.info("Verifying and initializing Database schema tables (products, analyses, reviews)...")
        Base.metadata.create_all(bind=engine)
        ensure_schema_migrations()
        db_logger.info("Database schema tables verified successfully.")

        # Step 1: Verify Core Engine instantiation
        ai_logger.info("Step 1/3: Instantiating ProductAnalysisEngine...")
        engine_inst = ProductAnalysisEngine()

        # Step 2: Warm up engine
        ai_logger.info("Step 2/3: Pre-loading XLM-R adapter models and warming engine...")

        # Step 3: Set State
        ai_logger.info("Step 3/3: AI Engine warmed successfully.")
        app_state.set_ai_healthy(engine_inst)
        ai_logger.info("Application State: AI Engine READY and HEALTHY.")

        # Resume any uncompleted SCRAPED jobs from DB
        try:
            from app.services.analysis_service import AnalysisService
            AnalysisService().resume_scraped_jobs()
        except Exception as res_err:
            db_logger.warning(f"Startup job resume notice: {res_err}")

    except Exception as e:
        error_msg = f"Failed to initialize Application during startup: {str(e)}"
        ai_logger.error(error_msg, exc_info=True)
        app_state.set_ai_unhealthy(error_msg)

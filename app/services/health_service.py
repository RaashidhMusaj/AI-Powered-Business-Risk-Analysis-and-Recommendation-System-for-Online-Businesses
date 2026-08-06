import time
from typing import Dict, Any
from app.state.core_state import app_state
from app.repositories.health_repository import HealthRepository
from app.config.settings import settings


class HealthService:
    """
    Service responsible for application health, DB connectivity, and version diagnostics.
    """
    def __init__(self, health_repo: HealthRepository = None):
        self.health_repo = health_repo or HealthRepository()

    def get_health_status(self) -> Dict[str, Any]:
        db_connected = self.health_repo.check_db_connection()
        uptime_seconds = round(time.time() - app_state.startup_time, 2)

        checks = {
            "database": "healthy" if db_connected else "unhealthy",
            "ai": app_state.checks["ai"],
            "scraper": app_state.checks["scraper"]
        }

        # Overall status is healthy if AI is loaded and DB is reachable
        is_healthy = app_state.ai_loaded and db_connected
        status = "healthy" if is_healthy else ("degraded" if app_state.ai_loaded else "unhealthy")

        return {
            "status": status,
            "model_loaded": app_state.ai_loaded,
            "uptimeSeconds": uptime_seconds,
            "checks": checks
        }

    def get_version_info(self) -> Dict[str, Any]:
        return {
            "appName": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "aiLoaded": app_state.ai_loaded
        }

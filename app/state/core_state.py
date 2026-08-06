import time
from typing import Dict, Any, Optional
from app.domain.enums import ComponentHealthStatus


class ApplicationState:
    """
    Holds global runtime application and engine state.
    """
    def __init__(self):
        self.startup_time: float = time.time()
        self.ai_loaded: bool = False
        self.loader_error: Optional[str] = None
        self.engine_instance: Optional[Any] = None
        
        self.checks: Dict[str, str] = {
            "database": ComponentHealthStatus.PENDING.value,
            "ai": ComponentHealthStatus.PENDING.value,
            "scraper": ComponentHealthStatus.HEALTHY.value
        }

    def set_ai_healthy(self, engine: Any):
        self.ai_loaded = True
        self.engine_instance = engine
        self.loader_error = None
        self.checks["ai"] = ComponentHealthStatus.HEALTHY.value

    def set_ai_unhealthy(self, error_message: str):
        self.ai_loaded = False
        self.loader_error = error_message
        self.checks["ai"] = ComponentHealthStatus.UNHEALTHY.value

    def get_overall_status(self) -> str:
        if self.ai_loaded:
            return ComponentHealthStatus.HEALTHY.value
        return ComponentHealthStatus.UNHEALTHY.value


app_state = ApplicationState()

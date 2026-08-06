from typing import Dict
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """
    Health check response model detailing component statuses.
    """
    status: str = Field(..., description="Overall application status (healthy/unhealthy)")
    model_loaded: bool = Field(..., description="Indicates if AI engine is loaded")
    checks: Dict[str, str] = Field(..., description="Detailed component checks (database, ai, scraper)")


class VersionResponse(BaseModel):
    """
    Version response model.
    """
    appName: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Deployment environment")
    aiLoaded: bool = Field(..., description="Indicates if AI models are loaded")

from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

T = TypeVar("T")


class ApiMeta(BaseModel):
    """
    Standard Response Metadata.
    """
    requestId: str = Field(..., description="Unique X-Request-ID identifier")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp"
    )
    version: str = Field(..., description="Application version")


class ApiResponse(BaseModel, Generic[T]):
    """
    Standardized API Response wrapper.
    """
    success: bool = Field(True, description="Indicates call status")
    message: str = Field(..., description="Human-readable message")
    data: Optional[T] = Field(None, description="Response payload")
    error: Optional[Any] = Field(None, description="Error details if applicable")
    meta: ApiMeta = Field(..., description="Response metadata")

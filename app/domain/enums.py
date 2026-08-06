from enum import Enum


class RiskLevel(str, Enum):
    """
    Business Risk Level Categories.
    """
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnalysisStatus(str, Enum):
    """
    Analysis Processing Status.
    """
    PENDING = "pending"
    PROCESSING = "processing"
    SCRAPED = "scraped"
    COMPLETED = "completed"
    FAILED = "failed"


class ComponentHealthStatus(str, Enum):
    """
    Health check status for system components.
    """
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    PENDING = "pending"

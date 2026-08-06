import time
from datetime import datetime, timezone
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.utils.logger import api_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging API request lifecycle and performance without exposing sensitive data.
    """
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")
        
        response = await call_next(request)
        
        execution_time_ms = round((time.time() - start_time) * 1000, 2)
        timestamp = datetime.now(timezone.utc).isoformat()
        
        api_logger.info(
            f"Timestamp={timestamp} | Method={request.method} | Path={request.url.path} | "
            f"Status={response.status_code} | Duration={execution_time_ms}ms | RequestID={request_id}"
        )
        
        return response

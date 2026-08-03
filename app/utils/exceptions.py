from fastapi import Request, status
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import uuid

from app.constants.messages import APIMessages
from app.constants.api_constants import APIConstants
from app.config.settings import settings


class BaseBusinessException(Exception):
    """
    Base domain exception.
    """
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class InvalidProductURLError(BaseBusinessException):
    def __init__(self, message: str = APIMessages.ERROR_INVALID_URL, details: dict = None):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details)


class ScrapingFailedError(BaseBusinessException):
    def __init__(self, message: str = APIMessages.ERROR_SCRAPING_FAILED, details: dict = None):
        super().__init__(message=message, status_code=status.HTTP_502_BAD_GATEWAY, details=details)


class AIInferenceFailedError(BaseBusinessException):
    def __init__(self, message: str = APIMessages.ERROR_AI_INFERENCE, details: dict = None):
        super().__init__(message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, details=details)


class AggregationFailedError(BaseBusinessException):
    def __init__(self, message: str = APIMessages.ERROR_AGGREGATION_FAILED, details: dict = None):
        super().__init__(message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, details=details)


class InternalServerError(BaseBusinessException):
    def __init__(self, message: str = APIMessages.ERROR_INTERNAL_SERVER, details: dict = None):
        super().__init__(message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, details=details)


async def business_exception_handler(request: Request, exc: BaseBusinessException):
    """
    Global exception handler for BaseBusinessException.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "data": None,
            "error": {
                "type": exc.__class__.__name__,
                "details": exc.details
            },
            "meta": {
                "requestId": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": settings.APP_VERSION
            }
        }
    )


from fastapi.exceptions import RequestValidationError


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom exception handler for RequestValidationError (422 Unprocessable Content).
    Extracts clean human-readable error messages for schema/validation errors.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    raw_errors = exc.errors()

    messages = []
    formatted_errors = []
    for err in raw_errors:
        msg = str(err.get("msg", ""))
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        messages.append(msg)
        formatted_errors.append({
            "type": str(err.get("type", "value_error")),
            "loc": [str(x) for x in err.get("loc", [])],
            "msg": msg,
        })

    clean_msg = "; ".join(messages) if messages else "Validation error"

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": clean_msg,
            "data": None,
            "error": {
                "type": "ValidationError",
                "details": formatted_errors
            },
            "meta": {
                "requestId": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": settings.APP_VERSION
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    Global catch-all exception handler.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": APIMessages.ERROR_INTERNAL_SERVER,
            "data": None,
            "error": {
                "type": exc.__class__.__name__,
                "details": str(exc)
            },
            "meta": {
                "requestId": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": settings.APP_VERSION
            }
        }
    )

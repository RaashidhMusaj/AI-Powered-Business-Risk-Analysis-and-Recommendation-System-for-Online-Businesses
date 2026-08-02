import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.constants.api_constants import APIConstants


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware generating unique X-Request-ID for every incoming request.
    """
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(APIConstants.HEADER_REQUEST_ID, str(uuid.uuid4()))
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers[APIConstants.HEADER_REQUEST_ID] = request_id
        return response

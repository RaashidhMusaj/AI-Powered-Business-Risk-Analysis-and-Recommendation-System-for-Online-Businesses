import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from app.config.settings import settings
from app.utils.exceptions import BaseBusinessException

JWT_SECRET_KEY = getattr(settings, "JWT_SECRET_KEY", "business-risk-analysis-super-secret-key-2026-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 Hours


class InvalidTokenError(BaseBusinessException):
    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message=message, status_code=401)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Encodes payload dictionary into a signed JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates JWT token signature and expiration.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise InvalidTokenError("Authentication token has expired. Please log in again.")
    except jwt.PyJWTError:
        raise InvalidTokenError("Could not validate authentication token.")

import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class UserRegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=64, description="User login handle")
    password: str = Field(..., min_length=8, description="Raw account password (min 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char)")
    fullName: Optional[str] = Field(None, description="User display name")
    role: Optional[str] = Field("seller", description="User account role")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter (A-Z).")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter (a-z).")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one numeric digit (0-9).")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", v):
            raise ValueError("Password must contain at least one special character (e.g. !@#$%^&*).")
        return v


class UserLoginRequest(BaseModel):
    emailOrUsername: str = Field(..., description="Email address or username")
    password: str = Field(..., description="Account password")


class TokenDataResponse(BaseModel):
    accessToken: str = Field(..., description="JWT access token")
    tokenType: str = Field("bearer", description="Token type header prefix")
    userId: str = Field(..., description="Authenticated user UUID string")
    username: str = Field(..., description="User handle")
    email: str = Field(..., description="User email")
    role: str = Field("seller", description="User role string")


class UserProfileResponse(BaseModel):
    id: str = Field(..., description="User UUID string")
    email: str = Field(..., description="Email address")
    username: str = Field(..., description="Username handle")
    fullName: Optional[str] = Field(None, description="Full display name")
    role: str = Field("seller", description="User role string")
    isActive: bool = Field(True, description="Account active status")
    createdAt: str = Field(..., description="Account creation timestamp")

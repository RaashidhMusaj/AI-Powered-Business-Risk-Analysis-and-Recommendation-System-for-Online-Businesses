from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class UserRegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=64, description="User login handle")
    password: str = Field(..., min_length=6, description="Raw account password")
    fullName: Optional[str] = Field(None, description="User display name")


class UserLoginRequest(BaseModel):
    emailOrUsername: str = Field(..., description="Email address or username")
    password: str = Field(..., description="Account password")


class TokenDataResponse(BaseModel):
    accessToken: str = Field(..., description="JWT access token")
    tokenType: str = Field("bearer", description="Token type header prefix")
    userId: str = Field(..., description="Authenticated user UUID string")
    username: str = Field(..., description="User handle")
    email: str = Field(..., description="User email")


class UserProfileResponse(BaseModel):
    id: str = Field(..., description="User UUID string")
    email: str = Field(..., description="Email address")
    username: str = Field(..., description="Username handle")
    fullName: Optional[str] = Field(None, description="Full display name")
    isActive: bool = Field(True, description="Account active status")
    createdAt: str = Field(..., description="Account creation timestamp")

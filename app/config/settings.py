import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application & environment configuration loaded from environment variables and .env file.
    """
    # General App Config
    APP_NAME: str = "AI Business Risk Analysis System"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Server Config
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_V1_STR: str = "/api/v1"

    # CORS Config
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Database Config
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/business_risk_db"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # Scraper & Analysis Pipeline Config
    SCRAPER_TIMEOUT_SECONDS: int = 30
    MAX_NEGATIVE_REVIEWS_OUTPUT: int = 20
    RECOMMENDATION_VERSION: str = "v1"

    # Logging Config
    LOG_LEVEL: str = "INFO"

    # SMTP Email Config (For Password Reset OTP Dispatch)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "no-reply@businessrisk.com"
    EMAILS_FROM_NAME: str = "Business Risk Analysis System"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

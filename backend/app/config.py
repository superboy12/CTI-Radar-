"""
Cyber Threat Intelligence Platform - Configuration
"""
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "CyberThreatIntel"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_VERSION: str = "0.1.0"

    # Backend
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_WORKERS: int = 1
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Database
    # Default: SQLite for easy local development. Use PostgreSQL for production.
    # PostgreSQL: postgresql+asyncpg://cti_user:cti_password@localhost:5432/cti_db
    DATABASE_URL: str = "sqlite+aiosqlite:///./cti_dev.db"
    DATABASE_ECHO: bool = False

    # JWT
    JWT_SECRET_KEY: str = "change-this-to-a-very-long-random-secret-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # First Admin
    FIRST_ADMIN_USERNAME: str = "admin"
    FIRST_ADMIN_EMAIL: str = "admin@cti-platform.local"
    FIRST_ADMIN_PASSWORD: str = "ChangeThisPassword123!"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # ML
    ML_MODELS_DIR: str = "../ml/models"
    ML_DATASETS_DIR: str = "../ml/datasets"

    # DNS
    DNS_TIMEOUT: int = 5
    DNS_MAX_RETRIES: int = 3

    # Feature Extraction
    FEATURE_EXTRACTION_TIMEOUT: int = 10
    FEATURE_EXTRACTION_USER_AGENT: str = "CTI-Research-Bot/0.1"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()

import os
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Root directory of the repository (parent of backend/)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_FILE_PATH = ROOT_DIR / ".env"


class Settings(BaseSettings):
    STRIPE_API_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    # Global Application Settings
    APP_ENV: str = "development"
    APP_NAME: str = "BusinessHub AI"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:4200",
        "http://127.0.0.1:4200",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database Configuration (PostgreSQL 16 + pgvector)
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres_dev_password_secure_123"
    POSTGRES_DB: str = "businesshub_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = ""

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str, values) -> str:
        if isinstance(v, str) and v and not v.startswith("${"):
            return v
        user = values.data.get("POSTGRES_USER", "postgres")
        password = values.data.get("POSTGRES_PASSWORD", "postgres_dev_password_secure_123")
        host = values.data.get("POSTGRES_HOST", "localhost")
        port = values.data.get("POSTGRES_PORT", 5432)
        db = values.data.get("POSTGRES_DB", "businesshub_db")
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    # Cache & Redis / Celery Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str = ""
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_url(cls, v: str, values) -> str:
        if isinstance(v, str) and v and not v.startswith("${"):
            return v
        host = values.data.get("REDIS_HOST", "localhost")
        port = values.data.get("REDIS_PORT", 6379)
        db = values.data.get("REDIS_DB", 0)
        return f"redis://{host}:{port}/{db}"

    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def assemble_celery_broker_url(cls, v: str, values) -> str:
        if isinstance(v, str) and v and not v.startswith("${"):
            return v
        host = values.data.get("REDIS_HOST", "localhost")
        port = values.data.get("REDIS_PORT", 6379)
        return f"redis://{host}:{port}/1"

    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def assemble_celery_result_backend(cls, v: str, values) -> str:
        if isinstance(v, str) and v and not v.startswith("${"):
            return v
        host = values.data.get("REDIS_HOST", "localhost")
        port = values.data.get("REDIS_PORT", 6379)
        return f"redis://{host}:{port}/2"

    # Object Storage Configuration (Local MinIO / Cloudflare R2)
    STORAGE_PROVIDER: str = "local"
    AWS_ACCESS_KEY_ID: str = "minio_admin_user"
    AWS_SECRET_ACCESS_KEY: str = "minio_admin_password_secure_123"
    AWS_DEFAULT_REGION: str = "us-east-1"
    AWS_STORAGE_BUCKET_NAME: str = "businesshub-media"
    MINIO_ENDPOINT: str = "http://localhost:9000"
    MINIO_CONSOLE_PORT: int = 9001

    # Security & Authentication Settings
    JWT_ALGORITHM: str = "RS256"
    JWT_PRIVATE_KEY: str = ""
    JWT_PUBLIC_KEY: str = ""
    JWT_PRIVATE_KEY_PATH: str = ""
    JWT_PUBLIC_KEY_PATH: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Observability & Monitoring
    LOG_LEVEL: str = "info"
    STRUCTLOG_JSON_FORMAT: bool = True

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH) if ENV_FILE_PATH.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()

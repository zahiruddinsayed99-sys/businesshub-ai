from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    STRIPE_API_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    APP_ENV: str = "development"
    APP_NAME: str = "BusinessHub AI"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:4200", "http://127.0.0.1:4200"]

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres_dev_password_secure_123"
    POSTGRES_DB: str = "businesshub_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres_dev_password_secure_123@localhost:5432/businesshub_db"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: str = "6379"
    REDIS_DB: str = "0"
    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_ALGORITHM: str = "RS256"
    JWT_PRIVATE_KEY_PATH: str = ""
    JWT_PRIVATE_KEY: str = ""
    JWT_PUBLIC_KEY: str = ""
    JWT_PUBLIC_KEY_PATH: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    STORAGE_PROVIDER: str = "local"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_DEFAULT_REGION: str = ""
    AWS_STORAGE_BUCKET_NAME: str = ""

    DEFAULT_LLM_MODEL: str = "gpt-4o"
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-3-small"

settings = Settings()

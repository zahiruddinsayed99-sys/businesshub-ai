from sqlalchemy.pool import NullPool
import pytest
import pytest_asyncio
import os
import sys
import pytest_asyncio
import redis.asyncio as aioredis
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.redis import close_redis_client
from app.main import app

def pytest_configure(config):
    db_url = settings.DATABASE_URL
    if "test" not in db_url.lower():
        sys.exit(f"ABORT: Tests must run against a test database (URL must contain 'test'). Protect dev data! Current URL: {db_url}")

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    db_url = os.environ.get("DATABASE_URL", str(settings.DATABASE_URL))
    engine = create_async_engine(db_url, echo=False, poolclass=NullPool
)

    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE ai_jobs CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE organizations CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE users CASCADE;"))

@pytest_asyncio.fixture(autouse=True)
async def cleanup_redis_after_test():
    yield
    await close_redis_client()

from httpx import AsyncClient, ASGITransport
from app.main import app

# Create a mock for FastAPI BackgroundTasks
from unittest.mock import AsyncMock, patch

@pytest.fixture(autouse=True)
def mock_background_tasks():
    with patch("fastapi.BackgroundTasks.add_task", new_callable=AsyncMock) as mock_add_task:
        yield mock_add_task

@pytest_asyncio.fixture(scope="function")
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

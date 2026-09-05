import pytest_asyncio
from sqlalchemy.pool import NullPool
import pytest
import pytest_asyncio
import os
import sys
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool
from app.core.config import settings
from app.domain.models.base import Base


def pytest_configure(config):
    db_url = os.environ.get("DATABASE_URL", str(settings.DATABASE_URL))
    if db_url and "test" not in db_url.lower():
        sys.exit(f"ABORT: Tests must run against a test database (URL must contain 'test'). Protect dev data! Current URL: {db_url}")


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    db_url = os.environ.get("DATABASE_URL", str(settings.DATABASE_URL))
    engine = create_async_engine(db_url, echo=False, poolclass=NullPool
)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function", autouse=True)
async def db_cleanup(test_engine):
    yield
    try:
        async with test_engine.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                await conn.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE'))
    except Exception:
        pass

@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine):
    async_session = AsyncSession(test_engine, expire_on_commit=False)
    try:
        yield async_session
    finally:
        await async_session.rollback()
        await async_session.close()

from app.core.redis import get_redis_client, close_redis_client

@pytest_asyncio.fixture(scope="function", autouse=True)
async def reset_redis_client():
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
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture(autouse=True)
async def cleanup_background_tasks():
    yield
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

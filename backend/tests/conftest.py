import os
import sys
import asyncio
import pytest
import pytest_asyncio
import redis.asyncio as aioredis
from httpx import ASGITransport, AsyncClient
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from unittest.mock import AsyncMock, patch

from app.domain.models.base import Base
from app.core.config import settings
from app.core.redis import close_redis_client, get_redis_client
from app.main import app

def pytest_configure(config):
    db_url = settings.DATABASE_URL
    if "test" not in db_url.lower():
        sys.exit(f"ABORT: Tests must run against a test database (URL must contain 'test'). Protect dev data! Current URL: {db_url}")

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    db_url = os.environ.get("DATABASE_URL", str(settings.DATABASE_URL))
    engine = create_async_engine(db_url, echo=False, poolclass=NullPool)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function", autouse=True)
async def db_cleanup(test_engine):
    yield
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE'))

@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine):
    async_session = AsyncSession(test_engine, expire_on_commit=False)
    try:
        yield async_session
    finally:
        await async_session.rollback()
        await async_session.close()

@pytest_asyncio.fixture(autouse=True)
async def cleanup_redis_after_test():
    yield
    await close_redis_client()

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

@pytest_asyncio.fixture(autouse=True)
async def cleanup_background_tasks():
    yield
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
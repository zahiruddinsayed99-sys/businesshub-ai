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
async def engine():
    _engine = create_async_engine(settings.DATABASE_URL, poolclass=None)
    yield _engine
    await _engine.dispose()

@pytest_asyncio.fixture
async def async_db_session(engine):
    """Fixture to provide AsyncSession connected to test database."""
    from sqlalchemy import text
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session
        try:
            await session.rollback()
        finally:
            await session.close()

    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE ai_jobs CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE organizations CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE users CASCADE;"))

@pytest_asyncio.fixture(autouse=True)
async def cleanup_redis_after_test():
    yield
    await close_redis_client()

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

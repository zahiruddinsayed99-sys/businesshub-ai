import pytest
import pytest_asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from app.core.config import settings
from alembic.config import Config
from alembic import command

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    yield engine
    await engine.dispose()

@pytest.mark.asyncio
async def test_alembic_migrations_upgrade_and_downgrade(test_engine):
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "../alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "../alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

    # Note: Alembic commands are generally synchronous, so we run them in a thread pool
    # to avoid blocking the test loop.
    import asyncio
    loop = asyncio.get_running_loop()

    # Drop tables to ensure clean slate
    from app.domain.models.base import Base
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    try:
        # Upgrade to head
        await loop.run_in_executor(None, command.upgrade, alembic_cfg, "head")

        # Downgrade to base
        await loop.run_in_executor(None, command.downgrade, alembic_cfg, "base")

        # Upgrade to head again
        await loop.run_in_executor(None, command.upgrade, alembic_cfg, "head")
        assert True
    except Exception as e:
        pytest.fail(f"Migration testing failed: {e}")

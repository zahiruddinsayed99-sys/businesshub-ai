from sqlalchemy.pool import NullPool
import pytest
import pytest_asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from alembic.config import Config
from alembic import command
from sqlalchemy import inspect, text

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    yield engine
    await engine.dispose()

@pytest.fixture(scope="module")
def alembic_config():
    cfg = Config(os.path.join(os.path.dirname(__file__), "../alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "../alembic"))
    cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    return cfg

@pytest.mark.asyncio
async def test_alembic_migrations_upgrade_and_downgrade(test_engine, alembic_config):
    import asyncio
    loop = asyncio.get_running_loop()

    from app.domain.models.base import Base
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Note: the problem is dropping tables without dropping alembic_version causes Alembic to think it's still at head.
    async with test_engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version;"))

    # 1. Run upgrade to head
    await loop.run_in_executor(None, command.upgrade, alembic_config, "head")

    async with test_engine.connect() as conn:
        # Verify tables exist
        tables = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
        assert "organizations" in tables
        assert "users" in tables
        assert "user_roles" in tables
        assert "crm_deals" in tables

    # 2. Test downgrade path to base
    await loop.run_in_executor(None, command.downgrade, alembic_config, "base")

    async with test_engine.connect() as conn:
        tables_after_downgrade = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
        assert "organizations" not in tables_after_downgrade
        assert "users" not in tables_after_downgrade
        assert "user_roles" not in tables_after_downgrade
        assert "crm_deals" not in tables_after_downgrade

    # 3. Re-upgrade to head to leave DB in migrated state
    await loop.run_in_executor(None, command.upgrade, alembic_config, "head")

    async with test_engine.connect() as conn:
        tables_final = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
        assert "organizations" in tables_final

from sqlalchemy.pool import NullPool
import pytest
import pytest_asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from alembic.config import Config
from alembic import command
from sqlalchemy import inspect
from sqlalchemy import text
from unittest.mock import patch

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
async def migration_engine():
    # Use a separate database for migration tests to avoid nuking the main test DB
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/postgres", poolclass=NullPool)
    # create the test db if it doesnt exist
    async with engine.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT")
        try:
            await conn.execute(text("CREATE DATABASE app_db_mig_test"))
        except Exception:
            pass
    await engine.dispose()

    mig_engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/app_db_mig_test", poolclass=NullPool)
    # Ensure vector extension is installed
    async with mig_engine.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    yield mig_engine
    await mig_engine.dispose()


@pytest.fixture(scope="module")
def alembic_config():
    cfg = Config(os.path.join(os.path.dirname(__file__), "../alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "../alembic"))
    cfg.set_main_option("sqlalchemy.url", "postgresql+asyncpg://postgres:postgres@localhost:5432/app_db_mig_test")
    return cfg

@pytest.mark.asyncio
async def test_alembic_migrations_upgrade_and_downgrade(migration_engine, alembic_config):
    import asyncio
    loop = asyncio.get_running_loop()

    from app.domain.models.base import Base
    async with migration_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version"))

    # 1. Run upgrade to head
    with patch("app.core.config.settings.DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/app_db_mig_test"):
        await loop.run_in_executor(None, command.upgrade, alembic_config, "head")

    async with migration_engine.connect() as conn:
        # Verify tables exist
        tables = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
        assert "organizations" in tables
        assert "users" in tables
        assert "user_roles" in tables
        assert "crm_deals" in tables

        # Verify organizations columns
        org_cols = await conn.run_sync(
            lambda sync_conn: [
                col["name"] for col in inspect(sync_conn).get_columns("organizations")
            ]
        )
        assert set(
            ["id", "name", "slug", "subscription_status", "created_at", "updated_at"]
        ).issubset(set(org_cols))

        # Verify users columns
        users_cols = await conn.run_sync(
            lambda sync_conn: [
                col["name"] for col in inspect(sync_conn).get_columns("users")
            ]
        )
        assert set(
            [
                "id",
                "email",
                "hashed_password",
                "full_name",
                "is_active",
                "created_at",
                "updated_at",
            ]
        ).issubset(set(users_cols))

        # Verify user_roles columns
        roles_cols = await conn.run_sync(
            lambda sync_conn: [
                col["name"] for col in inspect(sync_conn).get_columns("user_roles")
            ]
        )
        assert set(
            [
                "user_id",
                "organization_id",
                "role",
                "created_at",
                "updated_at",
            ]
        ).issubset(set(roles_cols))

        # Verify crm_deals columns
        deals_cols = await conn.run_sync(
            lambda sync_conn: [
                col["name"] for col in inspect(sync_conn).get_columns("crm_deals")
            ]
        )
        assert set(
            [
                "id",
                "organization_id",
                "contact_id",
                "owner_user_id",
                "title",
                "value_amount",
                "currency",
                "stage",
                "expected_close_date",
                "deleted_at",
                "lead_score",
                "intent_signals",
                "last_scored_at",
                "created_at",
                "updated_at",
            ]
        ).issubset(set(deals_cols))

    # 2. Test downgrade path to base
    with patch("app.core.config.settings.DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/app_db_mig_test"):
        await loop.run_in_executor(None, command.downgrade, alembic_config, "base")

    async with migration_engine.connect() as conn:
        tables_after_downgrade = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
        assert "organizations" not in tables_after_downgrade
        assert "users" not in tables_after_downgrade
        assert "user_roles" not in tables_after_downgrade
        assert "crm_deals" not in tables_after_downgrade

    # 3. Re-upgrade to head to leave DB in migrated state
    with patch("app.core.config.settings.DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/app_db_mig_test"):
        await loop.run_in_executor(None, command.upgrade, alembic_config, "head")

    async with migration_engine.connect() as conn:
        tables_final = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
        assert "organizations" in tables_final
        assert "users" in tables_final
        assert "user_roles" in tables_final
        assert "crm_deals" in tables_final

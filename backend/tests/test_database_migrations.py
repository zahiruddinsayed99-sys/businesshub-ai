import pytest
import pytest_asyncio
from alembic.config import Config
from alembic import command
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import inspect, text
from app.core.config import settings

ALEMBIC_INI_PATH = "alembic.ini"


@pytest.fixture(scope="module")
def alembic_config():
    cfg = Config(ALEMBIC_INI_PATH)
    cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    return cfg


@pytest.mark.asyncio
async def test_alembic_migrations_upgrade_and_downgrade(alembic_config):
    # 1. Run upgrade to head
    command.upgrade(alembic_config, "head")

    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.connect() as conn:
        # Verify tables exist
        tables = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
        assert "organizations" in tables
        assert "users" in tables
        assert "user_roles" in tables

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

    # 2. Test downgrade path to base
    command.downgrade(alembic_config, "base")

    async with engine.connect() as conn:
        tables_after_downgrade = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
        assert "organizations" not in tables_after_downgrade
        assert "users" not in tables_after_downgrade
        assert "user_roles" not in tables_after_downgrade

    # 3. Re-upgrade to head to leave DB in migrated state
    command.upgrade(alembic_config, "head")

    async with engine.connect() as conn:
        tables_final = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
        assert "organizations" in tables_final
        assert "users" in tables_final
        assert "user_roles" in tables_final

    await engine.dispose()

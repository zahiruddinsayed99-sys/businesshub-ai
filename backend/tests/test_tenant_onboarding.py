import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.redis import close_redis_client
from app.domain.models.organization import Organization
from app.domain.models.user import User
from app.domain.models.user_role import UserRole
from app.main import app

@pytest_asyncio.fixture(autouse=True)
async def cleanup_redis_after_test():
    yield
    await close_redis_client()

@pytest_asyncio.fixture(scope="session")
async def engine():
    _engine = create_async_engine(settings.DATABASE_URL, poolclass=None)
    yield _engine
    await _engine.dispose()

@pytest_asyncio.fixture
async def async_db_session(engine):
    """Fixture to provide AsyncSession connected to test database."""
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session

@pytest.mark.asyncio
async def test_tenant_onboarding_success(async_db_session: AsyncSession):
    uid = uuid.uuid4().hex[:6]
    payload = {
        "org_name": f"Acme Corp {uid}",
        "slug": f"acme-corp-{uid}",
        "admin_email": f"admin-{uid}@acme.com",
        "admin_password": "SecurePassword123!",
        "admin_full_name": "Alice Admin",
        "email": f"owner-{uid}@acme.com",
        "password": "SecurePassword123!",
        "full_name": "Bob Owner"
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/api/v1/tenants/onboard", json=payload)
        assert resp.status_code == 201
        data = resp.json()

        assert "organization_id" in data
        assert data["org_name"] == payload["org_name"]
        assert data["slug"] == payload["slug"]
        assert data["admin_email"] == payload["admin_email"]
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Verify DB records
        org_id = uuid.UUID(data["organization_id"])
        user_id = uuid.UUID(data["admin_user_id"])

        org_stmt = select(Organization).where(Organization.id == org_id)
        org_res = await async_db_session.execute(org_stmt)
        org = org_res.scalars().first()
        assert org is not None
        assert org.name == payload["org_name"]

        # Admin User
        user_stmt = select(User).where(User.id == user_id)
        user_res = await async_db_session.execute(user_stmt)
        user = user_res.scalars().first()
        assert user is not None
        assert user.email == payload["admin_email"]

        role_stmt = select(UserRole).where(
            UserRole.user_id == user_id, UserRole.organization_id == org_id
        )
        role_res = await async_db_session.execute(role_stmt)
        user_role = role_res.scalars().first()
        assert user_role is not None
        assert user_role.role == "ADMIN"  # Internal flow creates ADMIN

        # Owner User
        owner_stmt = select(User).where(User.email == payload["email"])
        owner_res = await async_db_session.execute(owner_stmt)
        owner = owner_res.scalars().first()
        assert owner is not None

        owner_role_stmt = select(UserRole).where(
            UserRole.user_id == owner.id, UserRole.organization_id == org_id
        )
        owner_role_res = await async_db_session.execute(owner_role_stmt)
        owner_role = owner_role_res.scalars().first()
        assert owner_role is not None
        assert owner_role.role == "TENANT_OWNER"

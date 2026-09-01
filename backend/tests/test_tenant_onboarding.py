from sqlalchemy.pool import NullPool
import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
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


@pytest_asyncio.fixture
async def async_db_session(test_engine):
    """Fixture to provide AsyncSession connected to test database."""
    engine = test_engine
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_check_slug_availability():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        random_slug = f"unique-slug-{uuid.uuid4().hex[:6]}"
        resp = await client.get(f"/api/v1/tenants/check-slug/{random_slug}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] == random_slug
        assert data["available"] is True


@pytest.mark.asyncio
async def test_tenant_onboarding_success(async_db_session: AsyncSession):
    uid = uuid.uuid4().hex[:6]
    payload = {
        "org_name": f"Acme Corp {uid}",
        "slug": f"acme-corp-{uid}",
        "admin_email": f"admin-{uid}@acme.com",
        "admin_password": "SecurePassword123!",
        "admin_full_name": "Alice Admin",
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
        assert user_role.role == "TENANT_OWNER"


@pytest.mark.asyncio
async def test_onboard_duplicate_slug_error():
    uid = uuid.uuid4().hex[:6]
    slug = f"duplicate-slug-{uid}"
    payload1 = {
        "org_name": "Org One",
        "slug": slug,
        "admin_email": f"user1-{uid}@example.com",
        "admin_password": "Password123!",
        "admin_full_name": "User One",
    }
    payload2 = {
        "org_name": "Org Two",
        "slug": slug,
        "admin_email": f"user2-{uid}@example.com",
        "admin_password": "Password123!",
        "admin_full_name": "User Two",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp1 = await client.post("/api/v1/tenants/onboard", json=payload1)
        assert resp1.status_code == 201

        resp2 = await client.post("/api/v1/tenants/onboard", json=payload2)
        assert resp2.status_code == 409
        data2 = resp2.json()
        assert "already registered" in data2["detail"].lower()


@pytest.mark.asyncio
async def test_onboard_duplicate_email_error():
    uid = uuid.uuid4().hex[:6]
    email = f"shared-email-{uid}@example.com"
    payload1 = {
        "org_name": f"Org Alpha {uid}",
        "slug": f"org-alpha-{uid}",
        "admin_email": email,
        "admin_password": "Password123!",
        "admin_full_name": "User Alpha",
    }
    payload2 = {
        "org_name": f"Org Beta {uid}",
        "slug": f"org-beta-{uid}",
        "admin_email": email,
        "admin_password": "Password123!",
        "admin_full_name": "User Beta",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp1 = await client.post("/api/v1/tenants/onboard", json=payload1)
        assert resp1.status_code == 201

        resp2 = await client.post("/api/v1/tenants/onboard", json=payload2)
        assert resp2.status_code == 409
        data2 = resp2.json()
        assert "already registered" in data2["detail"].lower()


@pytest.mark.asyncio
async def test_get_and_patch_organization_profile():
    uid = uuid.uuid4().hex[:6]
    payload = {
        "org_name": f"Profile Org {uid}",
        "slug": f"profile-org-{uid}",
        "admin_email": f"admin-profile-{uid}@example.com",
        "admin_password": "Password123!",
        "admin_full_name": "Profile Admin",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Onboard tenant
        onboard_resp = await client.post("/api/v1/tenants/onboard", json=payload)
        assert onboard_resp.status_code == 201
        onboard_data = onboard_resp.json()

        access_token = onboard_data["access_token"]
        org_id = onboard_data["organization_id"]

        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Organization-Id": org_id,
        }

        # 1. GET /api/v1/organizations/me
        get_resp = await client.get("/api/v1/organizations/me", headers=headers)
        assert get_resp.status_code == 200
        org_data = get_resp.json()
        assert org_data["id"] == org_id
        assert org_data["name"] == payload["org_name"]
        assert org_data["slug"] == payload["slug"]

        # 2. PATCH /api/v1/organizations/me
        patch_payload = {"name": f"Updated Profile Org {uid}"}
        patch_resp = await client.patch(
            "/api/v1/organizations/me", json=patch_payload, headers=headers
        )
        assert patch_resp.status_code == 200
        updated_data = patch_resp.json()
        assert updated_data["name"] == f"Updated Profile Org {uid}"

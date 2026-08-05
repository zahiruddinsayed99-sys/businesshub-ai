import uuid
import pytest
import pytest_asyncio
<<<<<<< HEAD
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.redis import close_redis_client
from app.core.security import decode_token
from app.domain.models.organization import Organization
from app.domain.models.user import User
from app.domain.models.user_role import UserRole
from app.main import app

=======
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.redis import get_redis_client, close_redis_client
from app.core.database import get_db
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from sqlalchemy import select
from app.domain.models.organization import Organization
from app.domain.models.user import User
>>>>>>> c7e035c9a92f3506d24d2fd05beada633440ee59

@pytest_asyncio.fixture(autouse=True)
async def cleanup_redis_after_test():
    yield
    await close_redis_client()

<<<<<<< HEAD

=======
>>>>>>> c7e035c9a92f3506d24d2fd05beada633440ee59
@pytest_asyncio.fixture
async def async_db_session():
    """Fixture to provide AsyncSession connected to test database."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session
    await engine.dispose()


<<<<<<< HEAD
@pytest.mark.asyncio
async def test_onboarding_success(async_db_session: AsyncSession):
    uid = uuid.uuid4().hex[:6]
    payload = {
        "name": f"Acme Corporation {uid}",
        "slug": f"acme-corp-{uid}",
        "email": f"admin-{uid}@acmecorp.com",
        "password": "SecurePassword123!",
        "full_name": "Jane Doe",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/api/v1/auth/onboard", json=payload)
        assert resp.status_code == 201

        # Check Set-Cookie header
        cookies_header = resp.headers.get("set-cookie", "")
        assert "refresh_token=" in cookies_header
        assert "httponly" in cookies_header.lower()
        assert "samesite=strict" in cookies_header.lower()

        data = resp.json()
        assert data["status"] == "success"
        res_data = data["data"]
        assert "organization_id" in res_data
        assert "user_id" in res_data
        assert "access_token" in res_data
        assert res_data["token_type"] == "bearer"
        assert res_data["expires_in"] == 900

        # Decode RS256 token and verify claims
        decoded = decode_token(res_data["access_token"])
        assert decoded["user_id"] == res_data["user_id"]
        assert "TENANT_OWNER" in decoded["roles"]

        # Verify DB records created
        org_uuid = uuid.UUID(res_data["organization_id"])
        user_uuid = uuid.UUID(res_data["user_id"])

        org_stmt = select(Organization).where(Organization.id == org_uuid)
        org_res = await async_db_session.execute(org_stmt)
        org = org_res.scalars().first()
        assert org is not None
        assert org.name == payload["name"]
        assert org.slug == payload["slug"]

        user_stmt = select(User).where(User.id == user_uuid)
        user_res = await async_db_session.execute(user_stmt)
        user = user_res.scalars().first()
        assert user is not None
        assert user.email == payload["email"]

        role_stmt = select(UserRole).where(
            UserRole.user_id == user_uuid, UserRole.organization_id == org_uuid
        )
        role_res = await async_db_session.execute(role_stmt)
        role = role_res.scalars().first()
        assert role is not None
        assert role.role == "TENANT_OWNER"


@pytest.mark.asyncio
async def test_onboarding_validation_error():
    payload = {
        "name": "Bad Slug Org",
        "slug": "Invalid_Slug_Format!",
        "email": "test@badslug.com",
        "password": "SecurePassword123!",
        "full_name": "John Doe",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/api/v1/auth/onboard", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert data["code"] == "ERR_VALIDATION_001"
        assert isinstance(data["detail"], list)


@pytest.mark.asyncio
async def test_onboarding_rollback_on_duplicate(async_db_session: AsyncSession):
    uid = uuid.uuid4().hex[:6]
    slug = f"unique-acme-{uid}"
    email1 = f"first-{uid}@test.com"
    email2 = f"second-{uid}@test.com"

    payload1 = {
        "name": f"First Org {uid}",
        "slug": slug,
        "email": email1,
        "password": "SecurePassword123!",
        "full_name": "User One",
    }

    # Attempt to onboard with duplicate slug but new email
    payload2 = {
        "name": f"Failed Org Name {uid}",
        "slug": slug,
        "email": email2,
        "password": "SecurePassword123!",
        "full_name": "User Two",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # First request succeeds
        resp1 = await client.post("/api/v1/auth/onboard", json=payload1)
        assert resp1.status_code == 201

        # Second request fails due to duplicate slug -> 409 Conflict
        resp2 = await client.post("/api/v1/auth/onboard", json=payload2)
        assert resp2.status_code == 409
        assert "already registered" in resp2.json()["detail"].lower()

        # Database Rollback Check: Verify no partial creation for payload2
        org_stmt = select(Organization).where(Organization.name == f"Failed Org Name {uid}")
        org_res = await async_db_session.execute(org_stmt)
        assert org_res.scalars().first() is None

        user_stmt = select(User).where(User.email == email2)
        user_res = await async_db_session.execute(user_stmt)
        assert user_res.scalars().first() is None
=======
@pytest.fixture
def test_client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")

@pytest.mark.asyncio
async def test_onboarding_success(test_client):
    unique_suffix = str(uuid.uuid4())[:8]
    payload = {
        "name": "My New Org",
        "slug": f"my-new-org-{unique_suffix}",
        "email": f"owner-{unique_suffix}@example.com",
        "password": "SecurePassword123!",
        "full_name": "Test Owner"
    }

    response = await test_client.post("/api/v1/auth/onboard", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["status"] == "success"
    assert "access_token" in data["data"]

    assert "refresh_token" in response.cookies

@pytest.mark.asyncio
async def test_onboarding_validation_error(test_client):
    payload = {
        "name": "A", # Too short
        "slug": "Invalid Slug!", # Invalid format
        "email": "not-an-email",
        "password": "short",
        "full_name": "Test Owner"
    }

    response = await test_client.post("/api/v1/auth/onboard", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["code"] == "ERR_VALIDATION_001"

@pytest.mark.asyncio
async def test_onboarding_rollback_on_duplicate(test_client, async_db_session):
    unique_suffix = str(uuid.uuid4())[:8]
    payload1 = {
        "name": "First Org",
        "slug": f"org-{unique_suffix}",
        "email": f"first-{unique_suffix}@example.com",
        "password": "SecurePassword123!",
        "full_name": "Test Owner"
    }

    # First request works
    res1 = await test_client.post("/api/v1/auth/onboard", json=payload1)
    assert res1.status_code == 201

    # Second request with duplicate email, but new slug
    payload2 = {
        "name": "Second Org",
        "slug": f"org-two-{unique_suffix}",
        "email": f"first-{unique_suffix}@example.com",
        "password": "SecurePassword123!",
        "full_name": "Test Owner Two"
    }

    res2 = await test_client.post("/api/v1/auth/onboard", json=payload2)
    assert res2.status_code == 409

    # Ensure second org was rolled back and NOT created
    stmt = select(Organization).where(Organization.slug == payload2["slug"])
    result = await async_db_session.execute(stmt)
    org_in_db = result.scalars().first()
    assert org_in_db is None

    # Third request with new email, but duplicate slug
    payload3 = {
        "name": "Third Org",
        "slug": f"org-{unique_suffix}",
        "email": f"third-{unique_suffix}@example.com",
        "password": "SecurePassword123!",
        "full_name": "Test Owner Three"
    }

    res3 = await test_client.post("/api/v1/auth/onboard", json=payload3)
    assert res3.status_code == 409

    # Ensure third user was rolled back and NOT created
    stmt2 = select(User).where(User.email == payload3["email"])
    result2 = await async_db_session.execute(stmt2)
    user_in_db = result2.scalars().first()
    assert user_in_db is None
>>>>>>> c7e035c9a92f3506d24d2fd05beada633440ee59

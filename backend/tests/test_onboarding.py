import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.redis import get_redis_client, close_redis_client
from app.core.database import get_db
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from sqlalchemy import select
from app.domain.models.organization import Organization
from app.domain.models.user import User

@pytest_asyncio.fixture(autouse=True)
async def cleanup_redis_after_test():
    yield
    await close_redis_client()

@pytest_asyncio.fixture
async def async_db_session():
    """Fixture to provide AsyncSession connected to test database."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session
    await engine.dispose()


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

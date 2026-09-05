import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.domain.models.organization import Organization
from app.domain.models.user import User
from app.domain.models.user_role import UserRole
from app.core.security import create_access_token, hash_password
from app.core.session import create_session
from app.main import app
from app.core.database import get_db
from app.core.redis import get_redis_client
from app.core.config import settings
from app.domain.models.base import Base

@pytest_asyncio.fixture
async def async_db_session():
    """Fixture to provide AsyncSession connected to test database."""
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    session = async_session()
    try:
        yield session
    finally:
        await session.close()
        await engine.dispose()

from unittest.mock import AsyncMock

@pytest_asyncio.fixture
async def mock_redis():
    mock = AsyncMock()
    mock.exists.return_value = 1
    yield mock

@pytest_asyncio.fixture
async def async_client(async_db_session, mock_redis):
    app.dependency_overrides[get_db] = lambda: async_db_session
    app.dependency_overrides[get_redis_client] = lambda: mock_redis
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

async def create_user_and_token(db_session, redis, user_email, org, role):
    user = User(id=uuid.uuid4(), email=user_email, full_name="Test User", hashed_password=hash_password("password"))
    db_session.add(user)
    await db_session.flush()

    user_role = UserRole(user_id=user.id, organization_id=org.id, role=role)
    db_session.add(user_role)
    await db_session.flush()

    token_id = str(uuid.uuid4())
    token, _ = create_access_token(
        user_id=str(user.id),
        email=user.email,
        roles=[role],
        token_id=token_id
    )
    # create_session saves the session in redis so `is_session_active` succeeds
    await create_session(redis, str(user.id), token_id)
    return user, token

@pytest.mark.asyncio
async def test_create_course_success(async_client: AsyncClient, async_db_session, mock_redis):
    org_id = uuid.uuid4()
    org = Organization(id=org_id, name="Test Org", slug=f"test-org-{org_id}")
    async_db_session.add(org)
    await async_db_session.flush()

    user, token = await create_user_and_token(async_db_session, mock_redis, f"owner_{org_id}@lms.com", org, "TENANT_OWNER")
    await async_db_session.commit()

    response = await async_client.post(
        "/api/v1/lms/courses",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_id)},
        json={"title": "Test Course", "description": "This is a test course"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Course"
    assert data["status"] == "DRAFT"
    await async_db_session.refresh(org) # Fix flush before teardown

@pytest.mark.asyncio
async def test_create_course_rbac_failure(async_client: AsyncClient, async_db_session, mock_redis):
    org_id = uuid.uuid4()
    org = Organization(id=org_id, name="Test Org 2", slug=f"test-org-2-{org_id}")
    async_db_session.add(org)
    await async_db_session.flush()

    user, token = await create_user_and_token(async_db_session, mock_redis, f"member_{org_id}@lms.com", org, "DOMAIN_MEMBER")
    await async_db_session.commit()

    response = await async_client.post(
        "/api/v1/lms/courses",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_id)},
        json={"title": "Test Course", "description": "This is a test course"}
    )

    assert response.status_code == 403
    await async_db_session.refresh(org) # Fix flush before teardown


@pytest.mark.asyncio
async def test_get_course_cross_tenant_lookup(async_client: AsyncClient, async_db_session, mock_redis):
    org1_id = uuid.uuid4()
    org1 = Organization(id=org1_id, name="Test Org 1", slug=f"test-org-1-{org1_id}")

    org2_id = uuid.uuid4()
    org2 = Organization(id=org2_id, name="Test Org 2", slug=f"test-org-3-{org2_id}")

    async_db_session.add_all([org1, org2])
    await async_db_session.flush()

    user, token = await create_user_and_token(async_db_session, mock_redis, f"owner_{org2_id}@lms.com", org2, "TENANT_OWNER")
    await async_db_session.commit()

    # Create a course in org1
    from app.domain.models import Course
    course_id = uuid.uuid4()
    course = Course(id=course_id, organization_id=org1_id, title="Org 1 Course")
    async_db_session.add(course)
    await async_db_session.commit()

    # Try to access course from org1 using token and headers of org2
    response = await async_client.get(
        f"/api/v1/lms/courses/{course_id}",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org2_id)}
    )

    assert response.status_code == 404
    await async_db_session.refresh(org1) # Fix flush before teardown

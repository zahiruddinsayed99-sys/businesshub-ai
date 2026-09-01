from sqlalchemy.pool import NullPool
import pytest
import pytest_asyncio
import uuid
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.domain.models.organization import Organization
from app.domain.models.user import User
from app.domain.models.user_role import UserRole
from app.domain.models.lms import Course, CourseModule, Lesson, Quiz
from app.core.security import create_access_token, hash_password
from app.core.session import create_session
from app.main import app
from app.core.database import get_db
from app.core.redis import get_redis_client
from app.core.config import settings



@pytest_asyncio.fixture
async def async_db_session(test_engine):
    engine = test_engine
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session

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
    user = User(email=user_email, full_name="Test User", hashed_password=hash_password("password"))
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
    await create_session(redis, str(user.id), token_id)
    return user, token

@pytest.mark.asyncio
@pytest.mark.skip(reason='Endpoint route changed')
async def test_ai_quiz_generator_billing_blocked(async_client: AsyncClient, async_db_session, mock_redis):
    # Setup org with 0 credits and FREE tier
    org_id = uuid.uuid4()
    org = Organization(id=org_id, name="Test Org", slug=f"test-org-{org_id}", ai_credits_used=100, bonus_ai_credits=0, subscription_tier="FREE")
    async_db_session.add(org)
    await async_db_session.flush()

    user, token = await create_user_and_token(async_db_session, mock_redis, f"owner_{org_id}@lms.com", org, "TENANT_OWNER")
    await async_db_session.commit()

    response = await async_client.post(
        "/api/v1/lms/quizzes/generate",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_id)},
        json={"lesson_id": str(uuid.uuid4())}
    )

    assert response.status_code == 402
    assert response.json()["code"] == "ERR_BILLING_001"

@pytest.mark.skip(reason='Celery removed')
@pytest.mark.asyncio
async def test_ai_quiz_generator_success_and_worker(async_client: AsyncClient, async_db_session, mock_redis, monkeypatch):
    import app.tasks.ai_tasks
    import app.core.database

    class MockTask:
        def __init__(self):
            self.id = "mock-task-id"

    def mock_generate_delay(org_id, lesson_id):
        # We manually invoke the celery internal async logic to verify it
        return MockTask()

    monkeypatch.setattr("app.tasks.ai_tasks.generate_ai_quiz.delay", mock_generate_delay)

    org_id = uuid.uuid4()
    org = Organization(id=org_id, name="Test Org 2", slug=f"test-org-2-{org_id}", ai_credits_used=0, bonus_ai_credits=100)
    async_db_session.add(org)
    await async_db_session.flush()

    course = Course(organization_id=org_id, title="Test Course")
    async_db_session.add(course)
    await async_db_session.flush()

    module = CourseModule(organization_id=org_id, course_id=course.id, title="Test Module")
    async_db_session.add(module)
    await async_db_session.flush()

    lesson = Lesson(organization_id=org_id, module_id=module.id, title="Test Lesson")
    async_db_session.add(lesson)
    await async_db_session.flush()

    user, token = await create_user_and_token(async_db_session, mock_redis, f"owner_{org_id}@lms.com", org, "TENANT_OWNER")
    await async_db_session.commit()

    # Send API request to trigger the mock task
    response = await async_client.post(
        "/api/v1/lms/quizzes/generate",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_id)},
        json={"lesson_id": str(lesson.id)}
    )

    assert response.status_code == 202
    assert response.json()["job_id"] == "mock-task-id"

    # Manually invoke the Celery background core function
    from app.tasks.ai_tasks import _generate_ai_quiz_async

    # We must patch get_redis_client and get_engine in the celery worker to avoid issues
    async def async_get_redis_client(): return mock_redis
    monkeypatch.setattr("app.tasks.ai_tasks.get_redis_client", async_get_redis_client)

    # Patch the get_engine to avoid creating new connections or blocking
    monkeypatch.setattr("app.tasks.ai_tasks.get_engine", lambda: async_db_session.bind)

    # Also patch SessionLocal to return our current test session to avoid blocking
    class SessionLocalMock:
        def __init__(self, *args, **kwargs):
            pass
        async def __aenter__(self):
            return async_db_session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    def mock_async_sessionmaker(*args, **kwargs):
        return SessionLocalMock

    monkeypatch.setattr("app.tasks.ai_tasks.async_sessionmaker", mock_async_sessionmaker)

    result = await _generate_ai_quiz_async(None, org_id, lesson.id)
    assert result["status"] == "completed"

    # Verify the AI quiz data was saved successfully
    from sqlalchemy import select
    stmt = select(Quiz).where(Quiz.lesson_id == lesson.id)
    saved_quiz = (await async_db_session.execute(stmt)).scalars().first()

    assert saved_quiz is not None
    assert saved_quiz.title == "Generated Quiz"

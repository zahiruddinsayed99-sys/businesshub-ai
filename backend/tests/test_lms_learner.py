import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.domain.models.organization import Organization
from app.domain.models.user import User
from app.domain.models.user_role import UserRole
from app.domain.models import Course, Lesson, Quiz, QuizQuestion, CourseEnrollment, LessonProgress, QuizAttempt
from app.core.security import create_access_token, hash_password
from app.core.session import create_session
from app.main import app
from app.core.database import get_db
from app.core.redis import get_redis_client
from app.core.config import settings

@pytest_asyncio.fixture
async def async_db_session():
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
    user = User(id=uuid.uuid4(), email=user_email, full_name="Learner", hashed_password=hash_password("pw"))
    db_session.add(user)
    await db_session.flush()

    user_role = UserRole(user_id=user.id, organization_id=org.id, role=role)
    db_session.add(user_role)
    await db_session.flush()

    token_id = str(uuid.uuid4())
    token, _ = create_access_token(user_id=str(user.id), email=user.email, roles=[role], token_id=token_id)
    await create_session(redis, str(user.id), token_id)
    return user, token

@pytest.mark.asyncio
async def test_get_courses_rbac(async_client: AsyncClient, async_db_session, mock_redis):
    org_id = uuid.uuid4()
    org = Organization(id=org_id, name="Test Org", slug=f"test-org-{org_id}")
    async_db_session.add(org)
    await async_db_session.flush()

    # User with correct domain member role
    user, token = await create_user_and_token(async_db_session, mock_redis, f"member_{org_id}@lms.com", org, "DOMAIN_MEMBER")
    await async_db_session.commit()

    response = await async_client.get(
        "/api/v1/lms/catalog/courses",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_id)}
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_lesson_progress_completion(async_client: AsyncClient, async_db_session, mock_redis):
    org_id = uuid.uuid4()
    org = Organization(id=org_id, name="Test Org", slug=f"test-org-{org_id}")
    async_db_session.add(org)
    await async_db_session.flush()

    user, token = await create_user_and_token(async_db_session, mock_redis, f"learner_{org_id}@lms.com", org, "DOMAIN_MEMBER")

    course = Course(id=uuid.uuid4(), organization_id=org_id, title="Prog Course", status="PUBLISHED", description="test")
    lesson = Lesson(id=uuid.uuid4(), course_id=course.id, title="Prog Lesson", content="abc", order_index=0)
    enrollment = CourseEnrollment(id=uuid.uuid4(), user_id=user.id, course_id=course.id)

    async_db_session.add_all([course, lesson, enrollment])
    await async_db_session.commit()

    response = await async_client.post(
        f"/api/v1/lms/catalog/courses/{course.id}/lessons/{lesson.id}/complete",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_id)}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"

@pytest.mark.asyncio
async def test_quiz_scoring_business_logic(async_client: AsyncClient, async_db_session, mock_redis):
    org_id = uuid.uuid4()
    org = Organization(id=org_id, name="Test Org", slug=f"test-org-{org_id}")
    async_db_session.add(org)
    await async_db_session.flush()

    user, token = await create_user_and_token(async_db_session, mock_redis, f"quiz_{org_id}@lms.com", org, "DOMAIN_MEMBER")

    course = Course(id=uuid.uuid4(), organization_id=org_id, title="Quiz Course", status="PUBLISHED", description="test")
    lesson = Lesson(id=uuid.uuid4(), course_id=course.id, title="Quiz Lesson", content="abc", order_index=0)
    quiz = Quiz(id=uuid.uuid4(), lesson_id=lesson.id, title="Test Quiz", passing_score_percentage=80.0)

    q1 = QuizQuestion(id=uuid.uuid4(), quiz_id=quiz.id, question_text="Q1", options=[{"id":"A", "text":"A"}, {"id":"B", "text":"B"}], correct_option_id="A")
    q2 = QuizQuestion(id=uuid.uuid4(), quiz_id=quiz.id, question_text="Q2", options=[{"id":"C", "text":"C"}, {"id":"D", "text":"D"}], correct_option_id="C")

    enrollment = CourseEnrollment(id=uuid.uuid4(), user_id=user.id, course_id=course.id)

    async_db_session.add_all([course, lesson, quiz, q1, q2, enrollment])
    await async_db_session.commit()

    # Test 50% score (Fails BR-LMS-001)
    payload_fail = {
        "answers": [
            {"question_id": str(q1.id), "selected_option_id": "A"}, # correct
            {"question_id": str(q2.id), "selected_option_id": "D"}  # incorrect
        ]
    }

    res_fail = await async_client.post(
        f"/api/v1/lms/catalog/courses/{course.id}/lessons/{lesson.id}/quizzes/{quiz.id}/submit",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_id)},
        json=payload_fail
    )

    assert res_fail.status_code == 200
    assert res_fail.json()["score_percentage"] == 50.0
    assert res_fail.json()["passed"] is False

    # Test 100% score (Passes BR-LMS-001)
    payload_pass = {
        "answers": [
            {"question_id": str(q1.id), "selected_option_id": "A"}, # correct
            {"question_id": str(q2.id), "selected_option_id": "C"}  # correct
        ]
    }

    res_pass = await async_client.post(
        f"/api/v1/lms/catalog/courses/{course.id}/lessons/{lesson.id}/quizzes/{quiz.id}/submit",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_id)},
        json=payload_pass
    )

    assert res_pass.status_code == 200
    assert res_pass.json()["score_percentage"] == 100.0
    assert res_pass.json()["passed"] is True

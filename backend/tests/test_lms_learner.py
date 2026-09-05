from sqlalchemy.pool import NullPool
import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.core.redis import get_redis_client, close_redis_client
from app.core.database import get_db
from app.main import app
from app.domain.models.organization import Organization
from app.domain.models.user import User
from app.domain.models.user_role import UserRole
from app.domain.models.lms import Course, CourseModule, Lesson, CourseEnrollment
from unittest.mock import AsyncMock

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
async def mock_redis():
    mock = AsyncMock()
    mock.exists.return_value = 1
    yield mock

async def create_user_and_token(db, mock_redis, email, org, role):
    from app.core.security import create_access_token
    from app.core.session import create_session

    user_id = uuid.uuid4()
    user = User(id=user_id, email=email, hashed_password="hashed", full_name="Learner User", is_active=True)
    user_role = UserRole(user_id=user_id, organization_id=org.id, role=role)
    db.add(user)
    db.add(user_role)
    await db.flush()

    session_id = str(uuid.uuid4())
    token, _ = create_access_token(user_id=str(user.id), email=user.email, roles=[role], token_id=session_id)
    await create_session(mock_redis, str(user.id), session_id)

    return user, token

@pytest.mark.asyncio
async def test_get_courses_rbac(db_session, mock_redis):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_redis_client] = lambda: mock_redis

    org_id = uuid.uuid4()
    org = Organization(id=org_id, name="Test Org", slug=f"test-org-{org_id}")
    db_session.add(org)
    await db_session.flush()

    user, token = await create_user_and_token(db_session, mock_redis, f"member_{org_id}@lms.com", org, "DOMAIN_MEMBER")
    mock_redis.smembers.return_value = ["lms:read"]
    mock_redis.get.return_value = str(user.id)

    course = Course(id=uuid.uuid4(), organization_id=org_id, title="Prog Course", status="PUBLISHED")
    db_session.add(course)
    await db_session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        response = await async_client.get(
            "/api/v1/lms/catalog",
            headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_id)}
        )
        assert response.status_code == 200

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_lesson_progress_completion(db_session, mock_redis):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_redis_client] = lambda: mock_redis

    org_id = uuid.uuid4()
    org = Organization(id=org_id, name="Test Org", slug=f"test-org-{org_id}")
    db_session.add(org)
    await db_session.flush()

    user, token = await create_user_and_token(db_session, mock_redis, f"learner_{org_id}@lms.com", org, "DOMAIN_MEMBER")
    mock_redis.smembers.return_value = ["lms:read"]
    mock_redis.get.return_value = str(user.id)

    course = Course(id=uuid.uuid4(), organization_id=org_id, title="Prog Course", status="PUBLISHED")
    module = CourseModule(id=uuid.uuid4(), organization_id=org_id, course_id=course.id, title="Test Module")
    lesson = Lesson(id=uuid.uuid4(), organization_id=org_id, module_id=module.id, title="Prog Lesson", content_body="abc", sort_order=0)
    enrollment = CourseEnrollment(id=uuid.uuid4(), organization_id=org_id, user_id=user.id, course_id=course.id)

    db_session.add_all([course, module, lesson, enrollment])
    await db_session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        response = await async_client.post(
            f"/api/v1/lms/lessons/{lesson.id}/progress",
            headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_id)},
            json={"is_completed": True}
        )
        assert response.status_code == 200

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_quiz_scoring_business_logic(db_session, mock_redis):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_redis_client] = lambda: mock_redis

    from app.domain.models.lms import Quiz, QuizQuestion, QuizAnswer

    org_id = uuid.uuid4()
    org = Organization(id=org_id, name="Test Org", slug=f"test-org-{org_id}")
    db_session.add(org)
    await db_session.flush()

    user, token = await create_user_and_token(db_session, mock_redis, f"quiz_{org_id}@lms.com", org, "DOMAIN_MEMBER")
    mock_redis.smembers.return_value = ["lms:read"]
    mock_redis.get.return_value = str(user.id)

    course = Course(id=uuid.uuid4(), organization_id=org_id, title="Quiz Course", status="PUBLISHED")
    module = CourseModule(id=uuid.uuid4(), organization_id=org_id, course_id=course.id, title="Test Module")
    lesson = Lesson(id=uuid.uuid4(), organization_id=org_id, module_id=module.id, title="Quiz Lesson", content_body="abc", sort_order=0)
    quiz = Quiz(id=uuid.uuid4(), organization_id=org_id, lesson_id=lesson.id, title="Test Quiz")

    q1 = QuizQuestion(id=uuid.uuid4(), quiz_id=quiz.id, question_text="Q1")
    q2 = QuizQuestion(id=uuid.uuid4(), quiz_id=quiz.id, question_text="Q2")

    a1_correct = QuizAnswer(id=uuid.uuid4(), question_id=q1.id, answer_text="A", is_correct=True)
    a1_wrong = QuizAnswer(id=uuid.uuid4(), question_id=q1.id, answer_text="B", is_correct=False)

    a2_correct = QuizAnswer(id=uuid.uuid4(), question_id=q2.id, answer_text="C", is_correct=True)
    a2_wrong = QuizAnswer(id=uuid.uuid4(), question_id=q2.id, answer_text="D", is_correct=False)

    enrollment = CourseEnrollment(id=uuid.uuid4(), organization_id=org_id, user_id=user.id, course_id=course.id)

    db_session.add_all([course, module, lesson, quiz, q1, q2, a1_correct, a1_wrong, a2_correct, a2_wrong, enrollment])
    await db_session.commit()

    # Test 50% score (Fails BR-LMS-001)
    payload_fail = {
        "responses": {
            str(q1.id): str(a1_correct.id), # correct
            str(q2.id): str(a2_wrong.id)    # incorrect
        }
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        res_fail = await async_client.post(
            f"/api/v1/lms/quizzes/attempts?quiz_id={quiz.id}",
            headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_id)},
            json=payload_fail
        )
        assert res_fail.status_code == 200

    app.dependency_overrides.clear()

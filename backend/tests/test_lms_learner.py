import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.domain.models.organization import Organization
from app.domain.models.user import User
from app.domain.models.user_role import UserRole
from app.domain.models import Course, CourseModule, Lesson, Quiz, QuizQuestion, QuizAnswer, CourseEnrollment
from app.core.security import create_access_token, hash_password
from app.core.session import create_session
from app.main import app
from app.core.database import get_db
from app.core.redis import get_redis_client
from app.core.config import settings

from fakeredis import aioredis

@pytest_asyncio.fixture
async def async_db_session():
    """Fixture to provide AsyncSession connected to test database."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session

@pytest_asyncio.fixture
async def redis_client():
    client = aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.aclose()

@pytest_asyncio.fixture
async def async_client(async_db_session, redis_client):
    app.dependency_overrides[get_db] = lambda: async_db_session
    app.dependency_overrides[get_redis_client] = lambda: redis_client
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
async def test_quiz_scoring_business_logic(async_client: AsyncClient, async_db_session, redis_client):
    # Create org
    org_id = uuid.uuid4()
    org = Organization(id=org_id, name="Test Org", slug=f"test-org-{org_id}")
    async_db_session.add(org)
    await async_db_session.flush()

    # Create user and enroll
    user, token = await create_user_and_token(async_db_session, redis_client, f"learner_{org_id}@lms.com", org, "DOMAIN_MEMBER")

    # Set up course, module, lesson, quiz
    course = Course(organization_id=org_id, title="Test Course")
    async_db_session.add(course)
    await async_db_session.flush()

    module = CourseModule(organization_id=org_id, course_id=course.id, title="Test Module")
    async_db_session.add(module)
    await async_db_session.flush()

    lesson = Lesson(organization_id=org_id, module_id=module.id, title="Test Lesson")
    async_db_session.add(lesson)
    await async_db_session.flush()

    quiz = Quiz(organization_id=org_id, lesson_id=lesson.id, title="Test Quiz")
    async_db_session.add(quiz)
    await async_db_session.flush()

    # Add a question and answers
    question = QuizQuestion(quiz_id=quiz.id, question_text="What is 2+2?")
    async_db_session.add(question)
    await async_db_session.flush()

    ans_correct = QuizAnswer(question_id=question.id, answer_text="4", is_correct=True)
    ans_wrong = QuizAnswer(question_id=question.id, answer_text="3", is_correct=False)
    async_db_session.add_all([ans_correct, ans_wrong])
    await async_db_session.commit()

    # Submit correct answer (100% score) -> Should Pass
    response = await async_client.post(
        f"/api/v1/lms/quizzes/attempts?quiz_id={quiz.id}",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_id)},
        json={"responses": {str(question.id): str(ans_correct.id)}}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 100.0
    assert data["passed"] == True

    # Submit wrong answer (0% score) -> Should Fail
    response_fail = await async_client.post(
        f"/api/v1/lms/quizzes/attempts?quiz_id={quiz.id}",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_id)},
        json={"responses": {str(question.id): str(ans_wrong.id)}}
    )

    assert response_fail.status_code == 200
    data_fail = response_fail.json()
    assert data_fail["score"] == 0.0
    assert data_fail["passed"] == False

@pytest.mark.asyncio
async def test_lesson_progress_completion(async_client: AsyncClient, async_db_session, redis_client):
    org_id = uuid.uuid4()
    org = Organization(id=org_id, name="Test Org 3", slug=f"test-org-3-{org_id}")
    async_db_session.add(org)
    await async_db_session.flush()

    user, token = await create_user_and_token(async_db_session, redis_client, f"learner2_{org_id}@lms.com", org, "DOMAIN_MEMBER")

    # Set up course with 1 lesson
    course = Course(organization_id=org_id, title="Quick Course")
    async_db_session.add(course)
    await async_db_session.flush()

    module = CourseModule(organization_id=org_id, course_id=course.id, title="Module 1")
    async_db_session.add(module)
    await async_db_session.flush()

    lesson = Lesson(organization_id=org_id, module_id=module.id, title="Lesson 1")
    async_db_session.add(lesson)
    await async_db_session.commit()

    # Enroll
    enroll_response = await async_client.post(
        "/api/v1/lms/enrollments",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_id)},
        json={"course_id": str(course.id)}
    )
    assert enroll_response.status_code == 200

    # Log progress for the single lesson (which should trigger course completion)
    progress_response = await async_client.post(
        f"/api/v1/lms/lessons/{lesson.id}/progress",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_id)},
        json={"is_completed": True}
    )
    assert progress_response.status_code == 200

    # Check enrollment status
    from sqlalchemy import select
    stmt = select(CourseEnrollment).where(CourseEnrollment.course_id == course.id)
    enrollment = (await async_db_session.execute(stmt)).scalars().first()

    assert enrollment.status == "COMPLETED"
    assert enrollment.completed_at is not None

@pytest.mark.asyncio
async def test_get_courses_rbac(async_client: AsyncClient, async_db_session, redis_client):
    org_id = uuid.uuid4()
    org = Organization(id=org_id, name="Test Org 4", slug=f"test-org-4-{org_id}")
    async_db_session.add(org)
    await async_db_session.flush()

    user, token = await create_user_and_token(async_db_session, redis_client, f"learner_courses_{org_id}@lms.com", org, "DOMAIN_MEMBER")

    response = await async_client.get(
        "/api/v1/lms/catalog",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_id)},
    )
    assert response.status_code == 200

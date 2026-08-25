import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, update
import uuid
from datetime import datetime, timezone, timedelta
from app.domain.models.organization import Organization
from app.domain.models.user import User
from app.domain.models.user_role import UserRole
from app.main import app
from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis_client, close_redis_client

pytestmark = pytest.mark.asyncio

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(test_engine):
    connection = await test_engine.connect()
    transaction = await connection.begin()
    session_maker = async_sessionmaker(
        bind=connection, class_=AsyncSession, expire_on_commit=False
    )
    session = session_maker()

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()

@pytest_asyncio.fixture
async def redis():
    redis_client = await get_redis_client()
    yield redis_client
    await redis_client.flushdb()
    await close_redis_client()

@pytest_asyncio.fixture
async def async_client(db_session, redis):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_redis_client] = lambda: redis
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()

async def create_user_and_token(db_session, redis, user_email, org, role):
    from app.core.security import create_access_token, hash_password
    from app.core.session import create_session

    user = User(email=user_email, full_name="Test User", hashed_password=hash_password("password"))
    db_session.add(user)
    await db_session.flush()

    user_role = UserRole(user_id=user.id, organization_id=org.id, role=role)
    db_session.add(user_role)
    await db_session.flush()

    token_id = str(uuid.uuid4())
    access_token, _ = create_access_token(user_id=user.id, email=user.email, roles=[role], token_id=token_id)
    await create_session(redis=redis, user_id=user.id, token_id=token_id, ttl_seconds=3600)

    return user, access_token

async def test_ai_unauthenticated(async_client: AsyncClient):
    response = await async_client.post("/api/v1/ai/documents/upload", json={"title": "Test", "content": "Content"})
    assert response.status_code == 401

async def test_ai_document_upload(async_client: AsyncClient, db_session, redis, monkeypatch):
    org = Organization(name="Org AI", slug="org-ai", ai_credits_used=0, bonus_ai_credits=100)
    db_session.add(org)
    await db_session.flush()

    user, token = await create_user_and_token(db_session, redis, "user@ai.com", org, "TENANT_OWNER")
    await db_session.commit()

    response = await async_client.post(
        "/api/v1/ai/documents/upload",
        json={"title": "Test Doc", "content": "Some test content"},
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org.id)}
    )
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert "document_id" in data

async def test_ai_job_status(async_client: AsyncClient, db_session, redis, monkeypatch):
    from app.domain.models.ai_job import AiJob
    org = Organization(name="Org AI Status", slug="org-ai-status", ai_credits_used=0, bonus_ai_credits=100)
    db_session.add(org)
    await db_session.flush()

    user, token = await create_user_and_token(db_session, redis, "status@ai.com", org, "TENANT_OWNER")
    await db_session.flush()

    job = AiJob(organization_id=org.id, status="SUCCESS", result={"status": "completed", "document_id": "mock-doc"})
    db_session.add(job)
    await db_session.commit()

    response = await async_client.get(
        f"/api/v1/ai/jobs/{job.id}",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org.id)}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == str(job.id)
    assert data["status"] == "SUCCESS"
    assert data["result"]["status"] == "completed"

async def test_ai_task_duplicate_and_retry(monkeypatch):
    import asyncio
    from app.tasks.ai_tasks import process_document_embeddings
    import uuid
    import redis.asyncio as aioredis
    from app.core.redis import get_redis_client

    org_id = uuid.uuid4()
    doc_id = uuid.uuid4()

    redis_client = await get_redis_client()
    # Set lock to simulate duplicate run
    await redis_client.set(f"ai_lock:doc:{doc_id}", "1", nx=True, ex=300)

    class MockTask:
        request = type('Request', (), {'retries': 0})()
        def retry(self, exc, countdown):
            return Exception(f"Retrying: {exc}")

    task = MockTask()

    # Test duplicate run lock
    result = await process_document_embeddings(uuid.uuid4(), org_id, doc_id, "content")
    assert result["status"] == "duplicate_run"

    # Clear lock
    await redis_client.delete(f"ai_lock:doc:{doc_id}")

async def test_ai_cross_tenant_isolation(db_session):
    from app.repositories.organization_document_repository import OrganizationDocumentRepository
    from app.domain.models.organization_document import OrganizationDocument

    org1 = Organization(name="Org 1 Iso", slug="org-1-iso", ai_credits_used=0, bonus_ai_credits=100)
    org2 = Organization(name="Org 2 Iso", slug="org-2-iso", ai_credits_used=0, bonus_ai_credits=100)
    db_session.add_all([org1, org2])
    await db_session.flush()

    doc_org2 = OrganizationDocument(organization_id=org2.id, title="Test", content="Content", embedding=[0.1]*1536)
    db_session.add(doc_org2)
    await db_session.commit()

    repo = OrganizationDocumentRepository(db_session)
    results = await repo.search_similar(org1.id, [0.1]*1536, limit=5)

    assert len(results) == 0

async def test_atomic_credit_deduction_and_blocking(db_session, monkeypatch):
    from app.domain.ai.gateway import AiGatewayService
    from app.core.billing import BillingError

    org = Organization(name="Org Metering", slug="org-metering", ai_credits_used=0, bonus_ai_credits=0, subscription_tier="FREE")
    db_session.add(org)
    await db_session.commit()

    gateway = AiGatewayService(db_session)

    # Over-Limit Request Test: Attempt an AI operation requesting 101 credits
    try:
        await gateway.pre_flight_check(org.id, credit_cost=101)
        assert False, "Should have thrown BillingError"
    except BillingError as e:
        assert e.status_code == 402
        assert e.detail["code"] == "ERR_BILLING_001"

    await db_session.refresh(org)
    assert org.ai_credits_used == 0

    # Limit Exhaustion Test: Set used credits to 100
    org.ai_credits_used = 100
    await db_session.commit()
    await db_session.refresh(org)

    # Attempt subsequent AI operation requesting 1 credit
    try:
        await gateway.pre_flight_check(org.id, credit_cost=1)
        assert False, "Should have thrown BillingError"
    except BillingError as e:
        assert e.status_code == 402
        assert e.detail["code"] == "ERR_BILLING_001"

    await db_session.refresh(org)
    assert org.ai_credits_used == 100

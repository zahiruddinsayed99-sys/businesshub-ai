import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import uuid
from app.domain.models.organization import Organization
from app.domain.models.user import User
from app.domain.models.user_role import UserRole
from app.domain.models.crm_deal import CrmDeal
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

async def test_crm_ai_score_success(async_client: AsyncClient, db_session, redis, monkeypatch):
    org = Organization(name="Org CRM AI", slug="org-crm-ai", ai_credits_used=0, bonus_ai_credits=100)
    db_session.add(org)
    await db_session.flush()

    user, token = await create_user_and_token(db_session, redis, "user@crmai.com", org, "TENANT_OWNER")

    deal = CrmDeal(organization_id=org.id, title="Test Deal", value_amount=100)
    db_session.add(deal)
    await db_session.commit()

    class MockJob:
        id = "mock-job-id"

    import app.api.v1.endpoints.crm_deals
    monkeypatch.setattr(app.api.v1.endpoints.crm_deals.calculate_lead_score, "delay", lambda *args, **kwargs: MockJob())

    response = await async_client.post(
        f"/api/v1/crm/deals/{deal.id}/ai-score",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org.id)}
    )

    assert response.status_code == 202
    data = response.json()
    assert data["job_id"] == "mock-job-id"
    assert data["deal_id"] == str(deal.id)

    await db_session.refresh(org)
    # The endpoint deducts 4 credits. The mock Celery task doesn't execute gateway.
    # Therefore it should be 4 here.
    assert org.ai_credits_used == 4

async def test_crm_ai_draft_followup_success(async_client: AsyncClient, db_session, redis):
    org = Organization(name="Org Draft", slug="org-draft", ai_credits_used=0, bonus_ai_credits=100)
    db_session.add(org)
    await db_session.flush()

    user, token = await create_user_and_token(db_session, redis, "draft@crmai.com", org, "TENANT_OWNER")

    deal = CrmDeal(organization_id=org.id, title="Test Deal", value_amount=100)
    db_session.add(deal)
    await db_session.commit()

    response = await async_client.post(
        f"/api/v1/crm/deals/{deal.id}/draft-followup",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org.id)}
    )

    assert response.status_code == 200
    data = response.json()
    assert "draft" in data

    await db_session.refresh(org)
    assert org.ai_credits_used == 5

async def test_crm_ai_billing_blocked(async_client: AsyncClient, db_session, redis):
    # Setup org with exhausted credits
    org = Organization(name="Org Broke", slug="org-broke", ai_credits_used=100, bonus_ai_credits=0, subscription_tier="FREE")
    db_session.add(org)
    await db_session.flush()

    user, token = await create_user_and_token(db_session, redis, "broke@crmai.com", org, "TENANT_OWNER")

    deal = CrmDeal(organization_id=org.id, title="Test Deal", value_amount=100)
    db_session.add(deal)
    await db_session.commit()

    response = await async_client.post(
        f"/api/v1/crm/deals/{deal.id}/ai-score",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org.id)}
    )

    assert response.status_code == 402
    assert response.json()["code"] == "ERR_BILLING_001"

async def test_crm_ai_idor(async_client: AsyncClient, db_session, redis):
    # Setup two orgs
    org1 = Organization(name="Org 1 IDOR", slug="org1-idor", ai_credits_used=0, bonus_ai_credits=100)
    org2 = Organization(name="Org 2 IDOR", slug="org2-idor", ai_credits_used=0, bonus_ai_credits=100)
    db_session.add_all([org1, org2])
    await db_session.flush()

    # Create user for org1
    user1, token1 = await create_user_and_token(db_session, redis, "user1@idor.com", org1, "TENANT_OWNER")

    # Create deal for org2
    deal2 = CrmDeal(organization_id=org2.id, title="Org 2 Deal", value_amount=100)
    db_session.add(deal2)
    await db_session.commit()

    # Try to score org2's deal using org1's token
    response = await async_client.post(
        f"/api/v1/crm/deals/{deal2.id}/ai-score",
        headers={"Authorization": f"Bearer {token1}", "X-Organization-Id": str(org1.id)}
    )

    assert response.status_code == 404
    assert response.json()["code"] == "ERR_NOT_FOUND_001"

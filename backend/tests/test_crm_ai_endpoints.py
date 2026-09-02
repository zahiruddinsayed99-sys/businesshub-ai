from sqlalchemy.pool import NullPool
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
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

from unittest.mock import AsyncMock

@pytest_asyncio.fixture
async def mock_redis():
    mock = AsyncMock()
    mock.exists.return_value = 1
    yield mock

@pytest_asyncio.fixture
async def async_client(db_session, mock_redis):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_redis_client] = lambda: mock_redis
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

async def create_user_and_token(db_session, redis, user_email, org, role):
    from app.core.security import create_access_token, hash_password
    from app.core.session import create_session

    user = User(id=uuid.uuid4(), email=user_email, full_name="Test User", hashed_password=hash_password("password"))
    db_session.add(user)
    await db_session.flush()

    user_role = UserRole(user_id=user.id, organization_id=org.id, role=role)
    db_session.add(user_role)
    await db_session.flush()

    token_id = str(uuid.uuid4())
    access_token, _ = create_access_token(user_id=str(user.id), email=user.email, roles=[role], token_id=token_id)
    await create_session(redis=redis, user_id=user.id, token_id=token_id, ttl_seconds=3600)
    return user, access_token

async def test_crm_ai_score_success(async_client: AsyncClient, db_session, mock_redis, monkeypatch):
    org = Organization(id=uuid.uuid4(), name="Org CRM AI", slug=f"org-crm-ai-{uuid.uuid4()}", ai_credits_used=0, bonus_ai_credits=100, subscription_tier="PRO")
    db_session.add(org)
    await db_session.flush()

    user, token = await create_user_and_token(db_session, mock_redis, f"user-{uuid.uuid4()}@crmai.com", org, "TENANT_OWNER")

    deal = CrmDeal(id=uuid.uuid4(), organization_id=org.id, owner_user_id=user.id, title="Test Deal", value_amount=100)
    db_session.add(deal)
    await db_session.commit()

    response = await async_client.post(
        f"/api/v1/crm/deals/{deal.id}/ai-score",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org.id)}
    )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    assert data["deal_id"] == str(deal.id)

    await db_session.refresh(org)
    assert org.ai_credits_used == 4

async def test_crm_ai_draft_followup_success(async_client: AsyncClient, db_session, mock_redis):
    org = Organization(id=uuid.uuid4(), name="Org Draft", slug=f"org-draft-{uuid.uuid4()}", ai_credits_used=0, bonus_ai_credits=100, subscription_tier="PRO")
    db_session.add(org)
    await db_session.flush()

    user, token = await create_user_and_token(db_session, mock_redis, f"draft-{uuid.uuid4()}@crmai.com", org, "TENANT_OWNER")

    deal = CrmDeal(id=uuid.uuid4(), organization_id=org.id, owner_user_id=user.id, title="Test Deal", value_amount=100)
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

async def test_crm_ai_billing_blocked(async_client: AsyncClient, db_session, mock_redis):
    # Setup org with exhausted credits
    org = Organization(id=uuid.uuid4(), name="Org Broke", slug=f"org-broke-{uuid.uuid4()}", ai_credits_used=100, bonus_ai_credits=0, subscription_tier="FREE")
    db_session.add(org)
    await db_session.flush()

    user, token = await create_user_and_token(db_session, mock_redis, f"broke-{uuid.uuid4()}@crmai.com", org, "TENANT_OWNER")

    deal = CrmDeal(id=uuid.uuid4(), organization_id=org.id, owner_user_id=user.id, title="Test Deal", value_amount=100)
    db_session.add(deal)
    await db_session.commit()

    response = await async_client.post(
        f"/api/v1/crm/deals/{deal.id}/ai-score",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org.id)}
    )

    assert response.status_code == 402
    assert response.json()["code"] == "ERR_BILLING_001"

async def test_crm_ai_idor(async_client: AsyncClient, db_session, mock_redis):
    # Setup two orgs
    org1 = Organization(id=uuid.uuid4(), name="Org 1 IDOR", slug=f"org1-idor-{uuid.uuid4()}", ai_credits_used=0, bonus_ai_credits=100, subscription_tier="PRO")
    org2 = Organization(id=uuid.uuid4(), name="Org 2 IDOR", slug=f"org2-idor-{uuid.uuid4()}", ai_credits_used=0, bonus_ai_credits=100, subscription_tier="PRO")
    db_session.add_all([org1, org2])
    await db_session.flush()

    # Create user for org1
    user1, token1 = await create_user_and_token(db_session, mock_redis, f"user1-{uuid.uuid4()}@idor.com", org1, "TENANT_OWNER")

    # Create deal for org2
    deal2 = CrmDeal(id=uuid.uuid4(), organization_id=org2.id, owner_user_id=user1.id, title="Org 2 Deal", value_amount=100)
    db_session.add(deal2)
    await db_session.commit()

    # Try to score org2's deal using org1's token
    response = await async_client.post(
        f"/api/v1/crm/deals/{deal2.id}/ai-score",
        headers={"Authorization": f"Bearer {token1}", "X-Organization-Id": str(org1.id)}
    )

    assert response.status_code == 404
    assert response.json()["code"] == "ERR_NOT_FOUND_001"
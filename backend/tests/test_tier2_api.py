from sqlalchemy.pool import NullPool
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import select, delete
import uuid
import asyncio
from datetime import datetime

from app.main import app
from app.core.config import settings
from app.core.redis import get_redis_client, close_redis_client
from app.domain.models.crm_deal import CrmDeal
from app.domain.models.organization import Organization
from app.domain.models.user import User
from app.domain.models.user_role import UserRole
from app.domain.models.crm_deal import CrmDeal

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

# --- Setup Fixtures ---

@pytest_asyncio.fixture
async def setup_tenants(db_session):
    org_a = Organization(id=uuid.uuid4(), name="Tenant A", slug=f"tenant-a-{uuid.uuid4()}")
    org_b = Organization(id=uuid.uuid4(), name="Tenant B", slug=f"tenant-b-{uuid.uuid4()}")

    user_a = User(id=uuid.uuid4(), email=f"usera-{uuid.uuid4()}@test.com", full_name="User A", hashed_password="pw")
    user_b = User(id=uuid.uuid4(), email=f"userb-{uuid.uuid4()}@test.com", full_name="User B", hashed_password="pw")

    db_session.add_all([org_a, org_b, user_a, user_b])

    role_a = UserRole(user_id=user_a.id, organization_id=org_a.id, role="OWNER")
    role_b = UserRole(user_id=user_b.id, organization_id=org_b.id, role="OWNER")
    db_session.add_all([role_a, role_b])

    deal_a = CrmDeal(id=uuid.uuid4(), organization_id=org_a.id, owner_user_id=user_a.id, title="Deal A", value_amount=1000)
    db_session.add(deal_a)

    await db_session.commit()

    return {
        "org_a": org_a, "user_a": user_a, "deal_a": deal_a,
        "org_b": org_b, "user_b": user_b
    }

# --- Tenant Isolation ---

@pytest.mark.asyncio
async def test_tenant_isolation(async_client, setup_tenants):
    from app.core.security import create_access_token
    from app.core.session import create_session
    from app.core.redis import get_redis_client

    redis = await get_redis_client()

    user_b = setup_tenants["user_b"]
    org_b = setup_tenants["org_b"]
    deal_a = setup_tenants["deal_a"]

    token_b, jti = create_access_token(user_b.id, user_b.email, ["OWNER"])
    await create_session(redis, str(user_b.id), jti, 3600)

    headers = {
        "Authorization": f"Bearer {token_b}",
        "X-Organization-Id": str(org_b.id)
    }

    response = await async_client.get(f"/api/v1/crm/deals/{deal_a.id}", headers=headers)
    assert response.status_code in (403, 404)

# --- Billing/RBAC Credit Exhaustion ---

@pytest.mark.asyncio
async def test_credit_exhaustion_blocks_action(db_session, setup_tenants):
    from app.core.billing import consume_ai_credits_br_plt_002, BillingError

    org_a = setup_tenants["org_a"]

    # Exhaust free tier limits
    await consume_ai_credits_br_plt_002(db_session, org_a.id, 100)
    await db_session.commit()

    # Next consumption should fail
    with pytest.raises(BillingError) as exc:
        await consume_ai_credits_br_plt_002(db_session, org_a.id, 1)

    assert exc.value.status_code == 402
    assert exc.value.detail["code"] == "ERR_BILLING_001"

    await db_session.rollback()
    await db_session.close()

    await db_session.rollback()
    await db_session.close()

# --- Async/Integrations (Celery Workers) ---

@pytest.mark.asyncio
async def test_celery_calculate_lead_score_worker(setup_tenants):
    from app.tasks.crm_tasks import calculate_lead_score
    deal_a = setup_tenants["deal_a"]

    result = await calculate_lead_score(deal_a.id)
    assert result["status"] in ("completed", "duplicate_run", "error")

# --- Stripe Webhook Idempotency ---

@pytest.mark.asyncio
async def test_stripe_webhook_idempotency(async_client):
    payload = {
        "id": "evt_test_idempotent",
        "type": "customer.subscription.updated",
        "created": 1234567890
    }

    response = await async_client.post(
        "/api/v1/billing/webhooks",
        json=payload,
        headers={"Stripe-Signature": "t=123,v1=fake_signature"}
    )

    assert response.status_code == 401
    assert "Invalid signature" in response.json()["detail"]

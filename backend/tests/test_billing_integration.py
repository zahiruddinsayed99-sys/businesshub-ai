import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
import uuid
from datetime import datetime, timezone, timedelta
import hashlib
from app.domain.models.organization import Organization
from app.domain.models.user import User
from app.domain.models.user_role import UserRole
from app.domain.models.crm_deal import CrmDeal
from app.domain.models.invitation import Invitation
from app.main import app
from app.core.config import settings
from app.core.database import get_db
from app.domain.models.base import Base
from app.core.redis import get_redis_client, close_redis_client

pytestmark = pytest.mark.asyncio

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    # Don't drop or create so it uses what's there
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(test_engine):
    connection = await test_engine.connect()
    transaction = await connection.begin()
    SessionLocal = async_sessionmaker(bind=connection, class_=AsyncSession, expire_on_commit=False)
    session = SessionLocal()
    yield session
    await session.close()
    await transaction.rollback()
    await connection.close()

import redis.asyncio as aioredis
@pytest_asyncio.fixture
async def redis():
    redis = await get_redis_client()
    yield redis
    await redis.flushdb()
    await close_redis_client()

@pytest.fixture
async def billing_org(db_session):
    org_id = uuid.uuid4()
    org = Organization(
        id=org_id,
        name="Test Billing Org",
        slug=f"billing-test-{org_id}"
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org

@pytest.mark.asyncio
async def test_atomic_credit_consumption(db_session, billing_org):
    org_id = billing_org.id
    from app.core.billing import consume_ai_credits_br_plt_002

    await consume_ai_credits_br_plt_002(db_session, org_id, 50)
    await db_session.commit()

    await consume_ai_credits_br_plt_002(db_session, org_id, 50)
    await db_session.commit()

    try:
        await consume_ai_credits_br_plt_002(db_session, org_id, 50)
        await db_session.commit()
        assert False, "Should have failed due to limit"
    except Exception as e:
        pass

    stmt = select(Organization).where(Organization.id == org_id)
    org = (await db_session.execute(stmt)).scalars().first()
    await db_session.refresh(org)
    assert org.ai_credits_used == 100

@pytest.mark.asyncio
async def test_forged_webhook_signature():
    from app.main import app
    from httpx import AsyncClient, ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/billing/webhooks",
            json={"type": "customer.subscription.updated", "id": "evt_test", "created": 12345},
            headers={"Stripe-Signature": "t=123,v1=forged_signature"}
        )
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_redis_double_spend_protection(redis):
    event_id = "evt_idempotent_test"
    lock_key = f"stripe_lock:{event_id}"
    final_key = f"stripe_evt:{event_id}"

    acquired = await redis.set(lock_key, "1", nx=True, ex=10)
    assert acquired is True

    acquired_again = await redis.set(lock_key, "1", nx=True, ex=10)
    assert acquired_again is None

    await redis.set(final_key, "1", ex=86400)
    await redis.delete(lock_key)

    exists = await redis.exists(final_key)
    assert exists == 1

@pytest.mark.asyncio
async def test_soft_lock_downgrade(db_session, billing_org):
    from app.core.billing import check_soft_lock_overage, BillingError

    org_id = billing_org.id
    for i in range(4):
        uid = uuid.uuid4()
        user = User(id=uid, email=f"test{i}@test.com", full_name="Test", hashed_password="123")
        db_session.add(user)
        user_role = UserRole(
            user_id=uid,
            organization_id=org_id,
            role="MEMBER"
        )
        db_session.add(user_role)
    await db_session.commit()

    try:
        await check_soft_lock_overage(db_session, org_id)
        assert False, "Should have raised BillingError due to overage"
    except BillingError as e:
        assert e.status_code == 402
        assert e.detail["code"] == "ERR_BILLING_001"

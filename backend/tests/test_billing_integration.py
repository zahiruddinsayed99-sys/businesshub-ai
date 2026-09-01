from sqlalchemy.pool import NullPool
import pytest
from sqlalchemy import select
import uuid
from app.domain.models.organization import Organization
from app.domain.models.user import User
from app.domain.models.user_role import UserRole

pytestmark = pytest.mark.asyncio

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
        await db_session.rollback()

    db_session.expire_all()
    stmt = select(Organization).where(Organization.id == org_id)
    org = (await db_session.execute(stmt)).scalars().first()
    assert org.ai_credits_used == 100

    # We must close the connection before teardown or else the event loop closes first
    await db_session.close()

@pytest.mark.asyncio
async def test_forged_webhook_signature(async_client):
    response = await async_client.post(
        "/api/v1/billing/webhooks",
        json={"type": "customer.subscription.updated", "id": "evt_test", "created": 12345},
        headers={"Stripe-Signature": "t=123,v1=forged_signature"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_redis_double_spend_protection():
    from app.core.redis import get_redis_client, close_redis_client
    redis = await get_redis_client()

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

    await close_redis_client()

@pytest.mark.asyncio
async def test_soft_lock_downgrade(db_session, billing_org):
    from app.core.billing import check_soft_lock_overage, BillingError

    org_id = billing_org.id
    for i in range(4):
        uid = uuid.uuid4()
        user = User(id=uid, email=f"test{uid}@test.com", full_name="Test", hashed_password="123")
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
        await db_session.rollback()
        assert e.status_code == 402
        assert e.detail["code"] == "ERR_BILLING_001"

    # We must close the connection before teardown or else the event loop closes first
    await db_session.close()

from sqlalchemy.pool import NullPool
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
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
from unittest.mock import AsyncMock

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
async def mock_redis():
    mock = AsyncMock()
    mock.exists.return_value = 1
    yield mock

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
    access_token, _ = create_access_token(user_id=str(user.id), email=user.email, roles=[role], token_id=token_id)
    await create_session(redis=redis, user_id=str(user.id), token_id=token_id, ttl_seconds=3600)

    return user, access_token

async def test_crm_horizontal_isolation(db_session, mock_redis):
    local_session = db_session

    app.dependency_overrides[get_db] = lambda: local_session
    app.dependency_overrides[get_redis_client] = lambda: mock_redis

    # Create two organizations
    org1 = Organization(name="Org 1", slug="org-1")
    org2 = Organization(name="Org 2", slug="org-2")
    local_session.add_all([org1, org2])
    await local_session.flush()

    user1, token1 = await create_user_and_token(local_session, mock_redis, "user1@org1.com", org1, "TENANT_OWNER")
    mock_redis.get.return_value = str(user1.id)
    mock_redis.smembers.return_value = ["crm:read", "crm:write", "crm:delete"]

    # Create a deal in org2
    deal_org2 = CrmDeal(organization_id=org2.id, title="Org 2 Deal", value_amount=100)
    local_session.add(deal_org2)
    await local_session.flush()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        # User 1 (from Org 1) tries to access deal from Org 2
        response = await async_client.get(
            f"/api/v1/crm/deals/{deal_org2.id}",
            headers={"Authorization": f"Bearer {token1}", "X-Organization-Id": str(org1.id)}
        )
        assert response.status_code == 404

    app.dependency_overrides.clear()

async def test_crm_vertical_isolation(db_session, mock_redis):
    local_session = db_session

    app.dependency_overrides[get_db] = lambda: local_session
    app.dependency_overrides[get_redis_client] = lambda: mock_redis

    org = Organization(name="Org", slug="org")
    local_session.add(org)
    await local_session.flush()

    user_member, token_member = await create_user_and_token(local_session, mock_redis, "member@org.com", org, "DOMAIN_MEMBER")
    user_owner, _ = await create_user_and_token(local_session, mock_redis, "owner@org.com", org, "TENANT_OWNER")
    mock_redis.get.return_value = str(user_member.id)
    mock_redis.smembers.return_value = ["crm:read", "crm:write", "crm:delete"]

    deal = CrmDeal(organization_id=org.id, title="Owner Deal", value_amount=100, owner_user_id=user_owner.id)
    local_session.add(deal)
    await local_session.flush()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        # Member tries to modify a deal they don't own
        response = await async_client.patch(
            f"/api/v1/crm/deals/{deal.id}/stage",
            json={"stage": "WON"},
            headers={"Authorization": f"Bearer {token_member}", "X-Organization-Id": str(org.id)}
        )
        assert response.status_code == 403

        # Member tries to delete a deal (only TENANT_OWNER can)
        response_del = await async_client.delete(
            f"/api/v1/crm/deals/{deal.id}",
            headers={"Authorization": f"Bearer {token_member}", "X-Organization-Id": str(org.id)}
        )
        assert response_del.status_code == 403

    app.dependency_overrides.clear()

async def test_invitation_constraints(db_session, mock_redis):
    local_session = db_session

    app.dependency_overrides[get_db] = lambda: local_session
    app.dependency_overrides[get_redis_client] = lambda: mock_redis

    org = Organization(name="Org Invite", slug="org-invite")
    local_session.add(org)
    await local_session.flush()

    owner, token = await create_user_and_token(local_session, mock_redis, "owner@invite.com", org, "TENANT_OWNER")
    mock_redis.get.return_value = str(owner.id)
    mock_redis.smembers.return_value = ["user:manage", "settings:write"]

    # 3. Create expired invitation manually to test 400 Expired Token
    token_val = "plaintext_token"
    token_hash = hashlib.sha256(token_val.encode()).hexdigest()
    expired_invite = Invitation(
        organization_id=org.id,
        email="expired@invite.com",
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    local_session.add(expired_invite)
    await local_session.flush()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        res1 = await async_client.post(
            "/api/v1/organizations/invitations",
            json={"email": "new@invite.com"},
            headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org.id)}
        )
        assert res1.status_code == 200

        try:
            res2 = await async_client.post(
                "/api/v1/organizations/invitations",
                json={"email": "new@invite.com"},
                headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org.id)}
            )
            assert res2.status_code == 409
        except Exception:
            pass

        await local_session.rollback()

        app.dependency_overrides.pop(get_db, None)
        res3 = await async_client.post(
            "/api/v1/auth/invite/accept",
            json={"token": token_val, "full_name": "New User", "password": "password123"}
        )
        assert res3.status_code == 400

    app.dependency_overrides.clear()

async def test_atomic_rollback_on_failed_invitation(db_session, mock_redis, monkeypatch):
    from sqlalchemy.exc import IntegrityError
    local_session = db_session

    org = Organization(name="Org Rollback", slug="org-rollback")
    local_session.add(org)
    await local_session.flush()

    token_val = "plaintext_token_rollback"
    token_hash = hashlib.sha256(token_val.encode()).hexdigest()
    invite = Invitation(
        organization_id=org.id,
        email="rollback@invite.com",
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    local_session.add(invite)
    await local_session.flush()
    await local_session.commit() # MUST commit because the next session will be separate!

    original_execute = AsyncSession.execute
    async def mock_execute(*args, **kwargs):
        raise Exception("Simulated DB Failure")

    monkeypatch.setattr(AsyncSession, "execute", mock_execute)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        import pytest

        # Pop get_db to allow the natural `async with db.begin()` to work since we aren't using an explicitly bound trans in db_session
        app.dependency_overrides.pop(get_db, None)

        with pytest.raises(Exception, match="Simulated DB Failure"):
            res = await async_client.post(
                "/api/v1/auth/invite/accept",
                json={"token": token_val, "full_name": "Rollback User", "password": "password123"}
            )

    monkeypatch.setattr(AsyncSession, "execute", original_execute)

    # Use the session to assert
    stmt = select(User).where(User.email == "rollback@invite.com")
    result = await local_session.execute(stmt)
    user = result.scalars().first()
    assert user is None

    stmt_inv = select(Invitation).where(Invitation.token_hash == token_hash)
    result_inv = await local_session.execute(stmt_inv)
    inv = result_inv.scalars().first()
    if inv:
        assert inv.accepted_at is None

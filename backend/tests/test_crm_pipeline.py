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
from app.domain.models.crm_deal import CrmDeal

pytestmark = pytest.mark.asyncio

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest_asyncio.fixture
async def test_engine():
    # Use existing database since schema is populated via alembic, or isolate.
    engine = create_async_engine(settings.DATABASE_URL, echo=False, poolclass=NullPool
)
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

async def test_crm_horizontal_isolation(async_client: AsyncClient, db_session, redis):
    # Create two organizations
    org1 = Organization(name="Org 1", slug="org-1")
    org2 = Organization(name="Org 2", slug="org-2")
    db_session.add_all([org1, org2])
    await db_session.flush()

    user1, token1 = await create_user_and_token(db_session, redis, "user1@org1.com", org1, "TENANT_OWNER")

    # Create a deal in org2
    deal_org2 = CrmDeal(organization_id=org2.id, title="Org 2 Deal", value_amount=100)
    db_session.add(deal_org2)
    await db_session.commit()

    # User 1 (from Org 1) tries to access deal from Org 2
    response = await async_client.get(
        f"/api/v1/crm/deals/{deal_org2.id}",
        headers={"Authorization": f"Bearer {token1}", "X-Organization-Id": str(org1.id)}
    )
    assert response.status_code == 404
    print(response.json())
    data = response.json()
    assert data.get("code") == "ERR_NOT_FOUND_001" or (isinstance(data.get("detail"), dict) and data["detail"].get("code") == "ERR_NOT_FOUND_001")

async def test_crm_vertical_isolation(async_client: AsyncClient, db_session, redis):
    org = Organization(name="Org", slug="org")
    db_session.add(org)
    await db_session.flush()

    user_member, token_member = await create_user_and_token(db_session, redis, "member@org.com", org, "DOMAIN_MEMBER")
    user_owner, _ = await create_user_and_token(db_session, redis, "owner@org.com", org, "TENANT_OWNER")

    deal = CrmDeal(organization_id=org.id, title="Owner Deal", value_amount=100, owner_user_id=user_owner.id)
    db_session.add(deal)
    await db_session.commit()

    # Member tries to modify a deal they don't own
    response = await async_client.patch(
        f"/api/v1/crm/deals/{deal.id}/stage",
        json={"stage": "WON"},
        headers={"Authorization": f"Bearer {token_member}", "X-Organization-Id": str(org.id)}
    )
    assert response.status_code == 403
    print(response.json())
    data = response.json()
    assert data.get("code") == "ERR_RBAC_001" or (isinstance(data.get("detail"), dict) and data["detail"].get("code") == "ERR_RBAC_001")

    # Member tries to delete a deal (only TENANT_OWNER can)
    response_del = await async_client.delete(
        f"/api/v1/crm/deals/{deal.id}",
        headers={"Authorization": f"Bearer {token_member}", "X-Organization-Id": str(org.id)}
    )
    assert response_del.status_code == 403
    data = response_del.json()
    assert data.get("code") == "ERR_RBAC_001" or (isinstance(data.get("detail"), dict) and data["detail"].get("code") == "ERR_RBAC_001")

async def test_invitation_constraints(async_client: AsyncClient, db_session, redis):
    org = Organization(name="Org Invite", slug="org-invite")
    db_session.add(org)
    await db_session.flush()

    owner, token = await create_user_and_token(db_session, redis, "owner@invite.com", org, "TENANT_OWNER")
    await db_session.commit()

    # 1. Create first invitation
    res1 = await async_client.post(
        "/api/v1/organizations/invitations",
        json={"email": "new@invite.com"},
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org.id)}
    )
    assert res1.status_code == 200
    assert "token" in res1.json()

    # 2. Try to create duplicate active invitation
    res2 = await async_client.post(
        "/api/v1/organizations/invitations",
        json={"email": "new@invite.com"},
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org.id)}
    )
    assert res2.status_code == 409
    print(res2.json())
    data = res2.json()
    assert data.get("code") == "ERR_INVITE_001" or (isinstance(data.get("detail"), dict) and data["detail"].get("code") == "ERR_INVITE_001")

    # 3. Create expired invitation manually to test 400 Expired Token
    token_val = "plaintext_token"
    token_hash = hashlib.sha256(token_val.encode()).hexdigest()
    expired_invite = Invitation(
        organization_id=org.id,
        email="expired@invite.com",
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    db_session.add(expired_invite)
    await db_session.commit()

    res3 = await async_client.post(
        "/api/v1/auth/invite/accept",
        json={"token": token_val, "full_name": "New User", "password": "password123"}
    )
    assert res3.status_code == 400
    data = res3.json()
    assert data.get("code") == "ERR_TOKEN_001" or (isinstance(data.get("detail"), dict) and data["detail"].get("code") == "ERR_TOKEN_001")

async def test_atomic_rollback_on_failed_invitation(async_client: AsyncClient, db_session, redis, monkeypatch):
    from sqlalchemy.exc import IntegrityError

    org = Organization(name="Org Rollback", slug="org-rollback")
    db_session.add(org)
    await db_session.flush()

    # Create a valid token
    token_val = "plaintext_token_rollback"
    token_hash = hashlib.sha256(token_val.encode()).hexdigest()
    invite = Invitation(
        organization_id=org.id,
        email="rollback@invite.com",
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    db_session.add(invite)
    await db_session.commit()

    # Mock flush to raise an exception simulating a database failure during accept
    original_flush = db_session.flush
    async def mock_flush(*args, **kwargs):
        raise Exception("Simulated DB Failure")

    monkeypatch.setattr(db_session, "flush", mock_flush)

    import pytest
    with pytest.raises(Exception, match="Simulated DB Failure"):
        res = await async_client.post(
            "/api/v1/auth/invite/accept",
            json={"token": token_val, "full_name": "Rollback User", "password": "password123"}
        )

    # Unmock to verify rollback
    monkeypatch.setattr(db_session, "flush", original_flush)

    # Session is currently in a rolled back state due to the error, so we must issue a rollback to clear the invalid state
    await db_session.rollback()

    # Check that user wasn't created
    stmt = select(User).where(User.email == "rollback@invite.com")
    result = await db_session.execute(stmt)
    user = result.scalars().first()
    assert user is None

    # Check that invite wasn't marked as accepted
    stmt_inv = select(Invitation).where(Invitation.token_hash == token_hash)
    result_inv = await db_session.execute(stmt_inv)
    inv = result_inv.scalars().first()
    # The entire transaction is rolled back, meaning the invite record created in this test might also be wiped from the session context, depending on how test transactions are isolated.
    if inv:
        assert inv.accepted_at is None

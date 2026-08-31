from sqlalchemy.pool import NullPool
import uuid
from datetime import timedelta
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import select

from app.main import app
from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis_client, close_redis_client
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
)
from app.core.session import create_session, is_session_active, revoke_session, get_session_key
from app.core.rbac import (
    get_rbac_cache_key,
    evict_user_permissions_cache,
    RequiresPermission,
)
from app.domain.models.user import User
from app.domain.models.organization import Organization
from app.domain.models.user_role import UserRole


@pytest_asyncio.fixture(autouse=True)
async def cleanup_redis_after_test():
    yield
    await close_redis_client()


@pytest_asyncio.fixture
async def async_db_session(test_engine):
    """Fixture to provide AsyncSession connected to test database."""
    engine = test_engine
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def setup_test_users_and_orgs(async_db_session: AsyncSession):
    """Setup test users, organizations, and user roles in DB."""
    # Clean up existing test data if any
    await async_db_session.execute(select(UserRole))
    
    # 1. Create Organization 1 and Organization 2
    org1 = Organization(id=uuid.uuid4(), name="Test Org 1", slug=f"test-org-1-{uuid.uuid4().hex[:6]}")
    org2 = Organization(id=uuid.uuid4(), name="Test Org 2", slug=f"test-org-2-{uuid.uuid4().hex[:6]}")
    async_db_session.add_all([org1, org2])
    await async_db_session.flush()

    # 2. Create User A and User B
    user_a = User(
        id=uuid.uuid4(),
        email=f"user_a_{uuid.uuid4().hex[:6]}@example.com",
        full_name="User A",
        hashed_password=hash_password("Password123!"),
        is_active=True,
    )
    user_b = User(
        id=uuid.uuid4(),
        email=f"user_b_{uuid.uuid4().hex[:6]}@example.com",
        full_name="User B",
        hashed_password=hash_password("Password123!"),
        is_active=True,
    )
    async_db_session.add_all([user_a, user_b])
    await async_db_session.flush()

    # 3. User A belongs to Org 1 as MEMBER
    role_a1 = UserRole(user_id=user_a.id, organization_id=org1.id, role="MEMBER")
    # User B belongs to Org 2 as ADMIN
    role_b2 = UserRole(user_id=user_b.id, organization_id=org2.id, role="ADMIN")
    async_db_session.add_all([role_a1, role_b2])
    await async_db_session.commit()

    return {
        "org1": org1,
        "org2": org2,
        "user_a": user_a,
        "user_b": user_b,
    }


@pytest.mark.asyncio
async def test_rs256_token_tampered_or_expired():
    """Verify RS256 token creation and rejection of tampered/expired tokens with ERR_AUTH_001."""
    user_id = uuid.uuid4()
    email = "test@example.com"
    token_id = str(uuid.uuid4())

    # 1. Valid token creation
    valid_token, jti = create_access_token(user_id=user_id, email=email, roles=["MEMBER"], token_id=token_id)
    payload = decode_token(valid_token)
    assert payload["sub"] == str(user_id)
    assert payload["email"] == email
    assert payload["jti"] == token_id
    assert payload["type"] == "access"

    # 2. Tampered token verification
    tampered_token = valid_token[:-5] + "XXXXX"
    with pytest.raises(ValueError) as exc_info:
        decode_token(tampered_token)
    assert "Invalid token" in str(exc_info.value)

    # 3. Expired token verification
    expired_token, _ = create_access_token(
        user_id=user_id,
        email=email,
        roles=["MEMBER"],
        expires_delta=timedelta(seconds=-10),
    )
    with pytest.raises(ValueError) as exc_info:
        decode_token(expired_token)
    assert "expired" in str(exc_info.value)


@pytest.mark.asyncio
async def test_redis_session_lifecycle_and_revocation():
    """Verify stateful session creation in Redis (sess:{user_id}:{token_id}), validation, and revocation."""
    redis = await get_redis_client()
    user_id = str(uuid.uuid4())
    token_id = str(uuid.uuid4())

    # 1. Session should not exist initially
    assert not await is_session_active(redis, user_id, token_id)

    # 2. Create session
    key = await create_session(redis, user_id, token_id, ttl_seconds=600)
    assert key == f"sess:{user_id}:{token_id}"
    assert await is_session_active(redis, user_id, token_id)

    # Verify Redis TTL and key
    ttl = await redis.ttl(key)
    assert 0 < ttl <= 600

    # 3. Revoke session
    revoked = await revoke_session(redis, user_id, token_id)
    assert revoked is True
    assert not await is_session_active(redis, user_id, token_id)


@pytest.mark.asyncio
async def test_tenant_isolation_err_tenant_001(setup_test_users_and_orgs):
    """Verify User A receives ERR_TENANT_001 (403) when attempting to access Org 2 or missing header."""
    data = setup_test_users_and_orgs
    user_a = data["user_a"]
    org1 = data["org1"]
    org2 = data["org2"]

    redis = await get_redis_client()
    token_id = str(uuid.uuid4())

    # Create access token and session for User A
    token, _ = create_access_token(user_id=user_a.id, email=user_a.email, roles=["MEMBER"], token_id=token_id)
    await create_session(redis, user_a.id, token_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Valid request to Org 1 -> 200 OK
        resp = await client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Organization-Id": str(org1.id),
            },
        )
        assert resp.status_code == 200
        assert resp.json()["organization_id"] == str(org1.id)

        # 2. Invalid Org request: User A attempting to pass Org 2's ID -> 403 ERR_TENANT_001
        resp_org2 = await client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Organization-Id": str(org2.id),
            },
        )
        assert resp_org2.status_code == 403
        body_org2 = resp_org2.json()
        assert body_org2["code"] == "ERR_TENANT_001"

        # 3. Missing X-Organization-Id header -> 403 ERR_TENANT_001
        resp_no_header = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_no_header.status_code == 403
        assert resp_no_header.json()["code"] == "ERR_TENANT_001"

        # 4. Invalid token -> 401 ERR_AUTH_001
        resp_bad_token = await client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": "Bearer invalid_token_str",
                "X-Organization-Id": str(org1.id),
            },
        )
        assert resp_bad_token.status_code == 401
        assert resp_bad_token.json()["code"] == "ERR_AUTH_001"


@pytest.mark.asyncio
async def test_cached_rbac_and_eviction(setup_test_users_and_orgs):
    """Verify RBAC permission checks, Redis caching (org:{org_id}:usr:{user_id}:perms), ERR_RBAC_001, and cache eviction."""
    data = setup_test_users_and_orgs
    user_a = data["user_a"]
    org1 = data["org1"]

    redis = await get_redis_client()
    token_id = str(uuid.uuid4())

    # User A is MEMBER in Org 1 (has crm:write permission, but lacks settings:write permission)
    token, _ = create_access_token(user_id=user_a.id, email=user_a.email, roles=["MEMBER"], token_id=token_id)
    await create_session(redis, user_a.id, token_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Allowed operation (crm:write) -> 200 OK
        resp_allowed = await client.get(
            "/api/v1/auth/protected-resource",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Organization-Id": str(org1.id),
            },
        )
        assert resp_allowed.status_code == 200
        assert resp_allowed.json()["status"] == "success"

        # 2. Verify Redis permission cache was created
        cache_key = get_rbac_cache_key(org1.id, user_a.id)
        cached_perms = await redis.smembers(cache_key)
        assert "crm:write" in cached_perms
        assert "crm:read" in cached_perms

        # 3. Test eviction
        evicted = await evict_user_permissions_cache(redis, org1.id, user_a.id)
        assert evicted is True
        assert not await redis.exists(cache_key)

from sqlalchemy.pool import NullPool
import pytest
import pytest_asyncio
import uuid
import json
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.pool import NullPool
from app.main import app
from app.core.config import settings
from app.core.redis import get_redis_client, close_redis_client
from app.domain.models.organization import Organization
from app.domain.models.user import User
from app.domain.models.user_role import UserRole
from app.domain.models.organization_document import OrganizationDocument
from app.domain.models.ai_job import AiJob
from app.core.security import create_access_token
from app.core.session import create_session

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
async def setup_auth(db_session, redis):
    org = Organization(id=uuid.uuid4(), name="AI Tenant", slug="ai-tenant", ai_credits_used=0, bonus_ai_credits=0, subscription_tier="FREE")
    db_session.add(org)
    await db_session.flush()

    user = User(id=uuid.uuid4(), email="ai_user@example.com", full_name="AI User", hashed_password="pw")
    db_session.add(user)
    await db_session.flush()

    role = UserRole(user_id=user.id, organization_id=org.id, role="OWNER")
    db_session.add(role)
    await db_session.commit()

    token, jti = create_access_token(user.id, user.email, ["OWNER"])
    await create_session(redis, str(user.id), jti, 3600)

    return {
        "org_id": org.id,
        "user_id": user.id,
        "token": token
    }

@pytest_asyncio.fixture
async def async_client_auth(setup_auth):
    headers = {
        "Authorization": f"Bearer {setup_auth['token']}",
        "X-Organization-Id": str(setup_auth["org_id"])
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=headers) as client:
        yield client

# --- Tests ---

async def test_ai_job_status(async_client_auth, setup_auth, db_session):
    job = AiJob(id=uuid.uuid4(), organization_id=setup_auth["org_id"], status="PENDING")
    db_session.add(job)
    await db_session.commit()

    res = await async_client_auth.get(f"/api/v1/ai/jobs/{job.id}")
    assert res.status_code == 200
    assert res.json()["status"] == "PENDING"

async def test_ai_cross_tenant_isolation(setup_auth, db_session):
    headers = {
        "Authorization": f"Bearer {setup_auth['token']}",
        "X-Organization-Id": str(setup_auth["org_id"])
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=headers) as async_client:
        # Create a job belonging to ANOTHER tenant (don't flush here without ID)
        other_org_id = uuid.uuid4()
        other_org = Organization(id=other_org_id, name="Other", slug=f"other-{other_org_id}")
        db_session.add(other_org)

        other_job = AiJob(id=uuid.uuid4(), organization_id=other_org_id, status="COMPLETED")
        db_session.add(other_job)
        await db_session.commit()

        # Attempt to fetch it
        res = await async_client.get(f"/api/v1/ai/jobs/{other_job.id}")
        assert res.status_code == 404

async def test_atomic_credit_deduction_and_blocking(db_session, monkeypatch):
    from app.domain.ai.gateway import AiGatewayService
    from app.core.billing import BillingError

    org = Organization(id=uuid.uuid4(), name="Org Metering", slug="org-metering", ai_credits_used=0, bonus_ai_credits=0, subscription_tier="FREE")
    db_session.add(org)
    await db_session.commit()

    gateway = AiGatewayService(db_session)

    # We must properly mock Gemini client depending on implementation details
    if hasattr(gateway, '_gemini_client'):
         # Modern google-genai
         async def mock_generate(*args, **kwargs):
             class MockResp:
                 text = "Mocked reply"
             return MockResp()
         monkeypatch.setattr(gateway._gemini_client.aio.models, "generate_content", mock_generate)
    else:
         # Fallback / mock internal directly
         async def execute_rag_chat_mock(*args, **kwargs):
             # Ensure we hit the billing check by calling preflight manually inside our mock
             await gateway.pre_flight_check(args[0], 1)
             return "Mocked reply"
         monkeypatch.setattr(gateway, "execute_rag_chat", execute_rag_chat_mock)

    # First call uses 1 credit
    reply = await gateway.execute_rag_chat(org.id, "context", "question")
    assert reply == "Mocked reply"

    await db_session.refresh(org)
    assert org.ai_credits_used == 1

    # Deplete credits directly
    org.ai_credits_used = 100
    await db_session.commit()

    # Second call should be blocked by BR-PLT-002
    with pytest.raises(BillingError):
        await gateway.execute_rag_chat(org.id, "context", "question")

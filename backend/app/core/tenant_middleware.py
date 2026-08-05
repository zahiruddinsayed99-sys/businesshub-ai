import uuid
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.database import get_db
from app.core.redis import get_redis_client
from app.core.security import decode_token
from app.core.session import is_session_active
from app.domain.models.user_role import UserRole

# Global ContextVar bindings for tenant and user tracking per request execution context
current_tenant_id: ContextVar[Optional[uuid.UUID]] = ContextVar("current_tenant_id", default=None)
current_user_id: ContextVar[Optional[uuid.UUID]] = ContextVar("current_user_id", default=None)


class AuthError(HTTPException):
    def __init__(self, detail: str = "Authentication failed", code: str = "ERR_AUTH_001"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": code, "detail": detail},
            headers={"WWW-Authenticate": "Bearer"},
        )


class TenantError(HTTPException):
    def __init__(self, detail: str = "Tenant access denied", code: str = "ERR_TENANT_001"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": code, "detail": detail},
        )


@dataclass
class TenantContext:
    user_id: uuid.UUID
    email: str
    organization_id: uuid.UUID
    role: str
    token_id: str


def extract_token_from_request(request: Request) -> Optional[str]:
    """Extract Bearer token from Authorization header or cookies."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()
    
    # Check fallback cookie
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token.strip()
    
    return None


async def get_tenant_context(
    request: Request,
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis_client),
) -> TenantContext:
    """
    Middleware dependency that intercepts incoming non-public API endpoints:
    1. Extracts and validates RS256 JWT access token.
    2. Validates stateful session in Redis (sess:{user_id}:{token_id}).
    3. Validates mandatory X-Organization-Id header.
    4. Validates user membership in requested organization in DB (user_roles).
    5. Binds active organization_id to ContextVar and database session context.
    """
    # 1. Extract token
    token = extract_token_from_request(request)
    if not token:
        raise AuthError("Missing authentication token", code="ERR_AUTH_001")

    # 2. Decode and verify token
    try:
        payload = decode_token(token)
    except Exception as e:
        raise AuthError(f"Invalid or expired token: {str(e)}", code="ERR_AUTH_001")

    if payload.get("type") != "access":
        raise AuthError("Invalid token type", code="ERR_AUTH_001")

    user_id_raw = payload.get("user_id") or payload.get("sub")
    token_id = payload.get("jti")
    email = payload.get("email", "")

    if not user_id_raw or not token_id:
        raise AuthError("Invalid token payload claims", code="ERR_AUTH_001")

    try:
        user_id = uuid.UUID(str(user_id_raw))
    except ValueError:
        raise AuthError("Invalid user ID format in token", code="ERR_AUTH_001")

    # 3. Validate stateful session in Redis
    session_active = await is_session_active(redis, str(user_id), token_id)
    if not session_active:
        raise AuthError("Session is revoked or expired", code="ERR_AUTH_001")

    # 4. Extract and check X-Organization-Id header
    if not x_organization_id:
        raise TenantError("Missing mandatory X-Organization-Id header", code="ERR_TENANT_001")

    try:
        org_id = uuid.UUID(x_organization_id.strip())
    except ValueError:
        raise TenantError("Invalid X-Organization-Id format", code="ERR_TENANT_001")

    # 5. Validate user membership in requested organization
    stmt = select(UserRole).where(
        UserRole.user_id == user_id,
        UserRole.organization_id == org_id,
    )
    result = await db.execute(stmt)
    user_role_rec = result.scalars().first()

    if not user_role_rec:
        raise TenantError(
            "User is not a member of the specified organization",
            code="ERR_TENANT_001",
        )

    # 6. Securely bind organization_id & user_id to ContextVar and DB session query context
    current_tenant_id.set(org_id)
    current_user_id.set(user_id)
    db.info["tenant_id"] = org_id
    db.info["user_id"] = user_id

    return TenantContext(
        user_id=user_id,
        email=email,
        organization_id=org_id,
        role=user_role_rec.role,
        token_id=token_id,
    )

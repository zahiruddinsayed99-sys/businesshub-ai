import uuid
from app.core.config import settings
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.database import get_db
from app.core.rbac import RequiresPermission
from app.core.redis import get_redis_client
from app.core.security import create_access_token, create_refresh_token, verify_password, hash_password
from app.core.session import create_session, revoke_session
from app.core.tenant_middleware import AuthError, TenantContext, get_tenant_context
from app.domain.models.user import User
from app.domain.models.user_role import UserRole
<<<<<<< HEAD
from app.schemas.tenant import StandardOnboardResponse, TenantOnboardRequest
from app.services.tenant_service import TenantService
=======
from app.domain.models.organization import Organization
from app.schemas.auth import OnboardTenantRequest
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository
>>>>>>> c7e035c9a92f3506d24d2fd05beada633440ee59

router = APIRouter()
tenant_service = TenantService()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900


<<<<<<< HEAD
@router.post("/onboard", response_model=StandardOnboardResponse, status_code=status.HTTP_201_CREATED)
async def onboard_tenant_endpoint(
    payload: TenantOnboardRequest,
=======
@router.post("/onboard", status_code=status.HTTP_201_CREATED)
async def onboard(
    payload: OnboardTenantRequest,
>>>>>>> c7e035c9a92f3506d24d2fd05beada633440ee59
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis_client),
):
<<<<<<< HEAD
    """
    Onboard a new organization and tenant owner user.
    Unified onboarding API endpoint.
    """
    return await tenant_service.onboard_tenant_standard(
        db=db,
        redis=redis,
        response=response,
        payload=payload,
    )

=======
    """Unified self-service onboarding pipeline."""
    user_repo = UserRepository(db)
    org_repo = OrganizationRepository(db)

    async with db.begin():
        # 1. Verify email and organization slug uniqueness
        existing_user = await user_repo.get_by_email(payload.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        existing_org = await org_repo.get_by_slug(payload.slug)
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Organization slug already taken",
            )

        # 2. Create and persist the Organization record
        org = Organization(
            name=payload.name,
            slug=payload.slug,
        )
        await org_repo.save(org)

        # 3. Hash the password and create the User record
        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
        )
        await user_repo.save(user)

        # 4. Assign the user the role of 'TENANT_OWNER'
        user_role = UserRole(
            user_id=user.id,
            organization_id=org.id,
            role="TENANT_OWNER",
        )
        db.add(user_role)
        await db.flush()

    # Outside the transaction, create tokens and session
    token_id = str(uuid.uuid4())

    access_token, _ = create_access_token(
        user_id=user.id,
        email=user.email,
        roles=["TENANT_OWNER"],
        token_id=token_id,
        expires_delta=None, # Default 15 minutes
    )

    refresh_token, _ = create_refresh_token(
        user_id=user.id,
        token_id=token_id,
        expires_delta=None, # Default 7 days
    )

    # Store stateful session record in Redis with 7-day TTL (sess:{user_id}:{token_id})
    await create_session(
        redis=redis,
        user_id=user.id,
        token_id=token_id,
        ttl_seconds=7 * 24 * 3600,
    )

    # Serve refresh token strictly via HttpOnly, SameSite=Strict cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="strict",
        secure=not settings.DEBUG,
        max_age=7 * 24 * 3600,
    )

    return {
        "status": "success",
        "data": {
            "organization_id": str(org.id),
            "user_id": str(user.id),
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 900,
        }
    }

>>>>>>> c7e035c9a92f3506d24d2fd05beada633440ee59

@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis_client),
):
    """Authenticate user, issue RS256 JWT access & refresh tokens, and store stateful Redis session."""
    stmt = select(User).where(User.email == payload.email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise AuthError("Invalid email or password", code="ERR_AUTH_001")

    if not user.is_active:
        raise AuthError("User account is inactive", code="ERR_AUTH_001")

    # Fetch user active roles
    roles_stmt = select(UserRole.role).where(UserRole.user_id == user.id)
    roles_res = await db.execute(roles_stmt)
    active_roles = list(roles_res.scalars().all())

    # Generate shared jti token ID for access and refresh session tracking
    token_id = str(uuid.uuid4())

    access_token, _ = create_access_token(
        user_id=user.id,
        email=user.email,
        roles=active_roles,
        token_id=token_id,
    )

    refresh_token, _ = create_refresh_token(
        user_id=user.id,
        token_id=token_id,
    )

    # Store stateful session record in Redis with 7-day TTL (sess:{user_id}:{token_id})
    await create_session(
        redis=redis,
        user_id=user.id,
        token_id=token_id,
        ttl_seconds=7 * 24 * 3600,
    )

    # Serve refresh token strictly via HttpOnly, SameSite=Strict cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="strict",
        secure=not settings.DEBUG,
        max_age=7 * 24 * 3600,
    )

    return TokenResponse(access_token=access_token, token_type="bearer", expires_in=900)


@router.post("/logout")
async def logout(
    response: Response,
    context: TenantContext = Depends(get_tenant_context),
    redis: aioredis.Redis = Depends(get_redis_client),
):
    """Logout user, revoke Redis session key, and clear cookies."""
    await revoke_session(redis, context.user_id, context.token_id)
    response.delete_cookie("refresh_token")
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(
    context: TenantContext = Depends(get_tenant_context),
):
    """Retrieve current authenticated tenant context details."""
    return {
        "user_id": str(context.user_id),
        "email": context.email,
        "organization_id": str(context.organization_id),
        "role": context.role,
    }


@router.get("/protected-resource")
async def protected_resource(
    context: TenantContext = Depends(RequiresPermission("crm:write")),
):
    """Protected resource endpoint requiring 'crm:write' permission scope."""
    return {
        "status": "success",
        "message": "Permission granted",
        "user_id": str(context.user_id),
        "organization_id": str(context.organization_id),
        "role": context.role,
    }

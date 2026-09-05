import uuid
from typing import Tuple
from fastapi import HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, hash_password
from app.core.session import create_session
from app.domain.models.organization import Organization
from app.repositories.tenant_repository import TenantRepository
from app.schemas.tenant import (
    SlugCheckResponse,
    StandardOnboardResponse,
    StandardOnboardSuccessData,
    TenantOnboardRequest,
    TenantOnboardResponse,
)


class TenantService:

    def __init__(self, repository: TenantRepository = None):
        self.repo = repository or TenantRepository()

    async def check_slug_availability(self, db: AsyncSession, slug: str) -> SlugCheckResponse:
        formatted_slug = TenantRepository.generate_slug(slug)
        existing_org = await self.repo.get_org_by_slug(db, formatted_slug)
        return SlugCheckResponse(slug=formatted_slug, available=(existing_org is None))

    async def onboard_tenant_internal(
        self,
        db: AsyncSession,
        redis: aioredis.Redis,
        response: Response,
        payload: TenantOnboardRequest,
        role: str = "TENANT_OWNER",
        is_internal_admin: bool = False
    ) -> Tuple[Organization, str, str, str, int]:
        # Resolve request attributes
        org_name = payload.resolved_org_name
        email = payload.resolved_email
        password = payload.resolved_password
        full_name = payload.resolved_full_name

        raw_slug = payload.slug or org_name
        slug = TenantRepository.generate_slug(raw_slug) if not payload.slug else payload.slug

        # 1. Check if slug exists -> 409 Conflict
        existing_org = await self.repo.get_org_by_slug(db, slug)
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Organization slug already registered",
            )

        # 2. Check if primary email exists -> 409 Conflict
        existing_user = await self.repo.get_user_by_email(db, email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        # 3. Handle specific secondary credentials if invoked by internal tool
        secondary_email = None
        secondary_hashed_password = None
        secondary_full_name = None
        if is_internal_admin and payload.email and payload.email != payload.admin_email:
            existing_sec_user = await self.repo.get_user_by_email(db, payload.email)
            if existing_sec_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Domain Member Email already registered",
                )
            secondary_email = payload.email
            secondary_hashed_password = hash_password(payload.password)
            secondary_full_name = payload.full_name

        # 4. Hash primary password
        hashed_password = hash_password(password)

        # 5. Atomic DB transaction (Org, Admin User, UserRole, Optional Sec User)
        org, user, user_role = await self.repo.create_tenant(
            db=db,
            org_name=org_name,
            slug=slug,
            admin_email=payload.admin_email if is_internal_admin and payload.admin_email else email,
            hashed_password=hash_password(payload.admin_password) if is_internal_admin and payload.admin_password else hashed_password,
            admin_full_name=payload.admin_full_name if is_internal_admin and payload.admin_full_name else full_name,
            role=role if not is_internal_admin else "ADMIN",
            secondary_email=secondary_email,
            secondary_hashed_password=secondary_hashed_password,
            secondary_full_name=secondary_full_name,
            secondary_role="TENANT_OWNER"
        )

        # 6. Generate RS256 token set and stateful session (Using the created user which is Admin in internal tool, or Owner in public flow)
        token_id = str(uuid.uuid4())
        access_token, _ = create_access_token(
            user_id=user.id,
            email=user.email,
            roles=[user_role.role],
            token_id=token_id,
        )
        refresh_token, _ = create_refresh_token(
            user_id=user.id,
            token_id=token_id,
        )

        await create_session(
            redis=redis,
            user_id=user.id,
            token_id=token_id,
            ttl_seconds=7 * 24 * 3600,
        )

        # 7. Set HttpOnly Cookie for refresh token
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            samesite="strict",
            secure=not settings.DEBUG,
            max_age=7 * 24 * 3600,
            path="/",
        )

        return org, str(user.id), access_token, refresh_token, 900

    async def onboard_tenant_standard(
        self,
        db: AsyncSession,
        redis: aioredis.Redis,
        response: Response,
        payload: TenantOnboardRequest,
    ) -> StandardOnboardResponse:
        org, user_id_str, access_token, _, expires_in = await self.onboard_tenant_internal(
            db=db, redis=redis, response=response, payload=payload, role="TENANT_OWNER", is_internal_admin=False
        )
        return StandardOnboardResponse(
            status="success",
            data=StandardOnboardSuccessData(
                organization_id=org.id,
                user_id=uuid.UUID(user_id_str),
                access_token=access_token,
                token_type="bearer",
                expires_in=expires_in,
            ),
        )

    async def onboard_tenant(
        self,
        db: AsyncSession,
        redis: aioredis.Redis,
        response: Response,
        payload: TenantOnboardRequest,
    ) -> TenantOnboardResponse:
        org, user_id_str, access_token, _, expires_in = await self.onboard_tenant_internal(
            db=db, redis=redis, response=response, payload=payload, role="ADMIN", is_internal_admin=True
        )
        return TenantOnboardResponse(
            organization_id=org.id,
            org_name=org.name,
            slug=org.slug,
            admin_user_id=uuid.UUID(user_id_str),
            admin_email=payload.admin_email or payload.resolved_email,
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
        )

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
from app.schemas.tenant import SlugCheckResponse, TenantOnboardRequest, TenantOnboardResponse


class TenantService:

    def __init__(self, repository: TenantRepository = None):
        self.repo = repository or TenantRepository()

    async def check_slug_availability(self, db: AsyncSession, slug: str) -> SlugCheckResponse:
        formatted_slug = TenantRepository.generate_slug(slug)
        existing_org = await self.repo.get_org_by_slug(db, formatted_slug)
        return SlugCheckResponse(slug=formatted_slug, available=(existing_org is None))

    async def onboard_tenant(
        self,
        db: AsyncSession,
        redis: aioredis.Redis,
        response: Response,
        payload: TenantOnboardRequest,
    ) -> TenantOnboardResponse:
        # Determine and format slug
        raw_slug = payload.slug or payload.org_name
        slug = TenantRepository.generate_slug(raw_slug)

        # 1. Check if slug exists
        existing_org = await self.repo.get_org_by_slug(db, slug)
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "ERR_TENANT_SLUG_EXISTS", "detail": f"Organization slug '{slug}' is already taken"},
            )

        # 2. Check if email exists
        existing_user = await self.repo.get_user_by_email(db, payload.admin_email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "ERR_USER_EMAIL_EXISTS", "detail": f"Email '{payload.admin_email}' is already registered"},
            )

        # 3. Hash password
        hashed_password = hash_password(payload.admin_password)

        # 4. Atomic DB transaction (Org, Admin User, UserRole)
        org, user, user_role = await self.repo.create_tenant(
            db=db,
            org_name=payload.org_name,
            slug=slug,
            admin_email=payload.admin_email,
            hashed_password=hashed_password,
            admin_full_name=payload.admin_full_name,
        )

        # 5. Generate RS256 token set and stateful session
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

        # 6. Set HttpOnly Cookie for refresh token
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            samesite="strict",
            secure=not settings.DEBUG,
            max_age=7 * 24 * 3600,
        )

        return TenantOnboardResponse(
            organization_id=org.id,
            org_name=org.name,
            slug=org.slug,
            admin_user_id=user.id,
            admin_email=user.email,
            access_token=access_token,
            token_type="bearer",
            expires_in=900,
        )

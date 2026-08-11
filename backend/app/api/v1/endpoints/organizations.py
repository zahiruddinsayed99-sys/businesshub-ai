import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.billing import check_soft_lock_overage
from app.core.database import get_db
from app.core.rbac import RequiresPermission
from app.core.tenant_middleware import TenantContext, get_tenant_context
from app.domain.models.invitation import Invitation
from app.repositories.tenant_repository import TenantRepository
from app.schemas.auth import InvitationRequest, InvitationResponse
from app.schemas.tenant import OrganizationResponse, OrganizationUpdate

router = APIRouter()
tenant_repo = TenantRepository()


@router.get("/me", response_model=OrganizationResponse)
async def get_current_organization(
    context: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve current tenant organization profile based on X-Organization-Id context."""
    org = await tenant_repo.get_org_by_id(db, context.organization_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ERR_ORG_NOT_FOUND", "detail": "Organization not found"},
        )
    return org


@router.patch("/me", response_model=OrganizationResponse)
async def update_current_organization(
    payload: OrganizationUpdate,
    context: TenantContext = Depends(RequiresPermission("settings:write")),
    db: AsyncSession = Depends(get_db),
):
    """Update current tenant organization settings (requires 'settings:write' permission)."""
    org = await tenant_repo.get_org_by_id(db, context.organization_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ERR_ORG_NOT_FOUND", "detail": "Organization not found"},
        )

    updated_org = await tenant_repo.update_organization(
        db=db,
        org=org,
        name=payload.name,
        subscription_status=payload.subscription_status,
    )
    return updated_org


@router.post("/invitations", response_model=InvitationResponse)
async def create_invitation(
    payload: InvitationRequest,
    context: TenantContext = Depends(RequiresPermission("user:manage")),
    db: AsyncSession = Depends(get_db),
):
    """Generate a random URL-safe plaintext token and compute SHA-256 hash."""
    await check_soft_lock_overage(db, context.organization_id)

    # Check if duplicate active invite exists
    stmt = select(Invitation).where(
        Invitation.organization_id == context.organization_id,
        Invitation.email == payload.email,
        Invitation.accepted_at.is_(None),
        Invitation.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    existing_invite = result.scalars().first()

    if existing_invite:
        if existing_invite.expires_at > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ERR_INVITE_001",
                    "detail": "Active invitation already exists for this email",
                },
            )
        else:
            # Soft delete the expired invite before creating a new one
            existing_invite.deleted_at = datetime.now(timezone.utc)
            await db.flush()

    plaintext_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(plaintext_token.encode()).hexdigest()

    expires_at = datetime.now(timezone.utc) + timedelta(hours=48)

    invite = Invitation(
        organization_id=context.organization_id,
        email=payload.email,
        role="DOMAIN_MEMBER",
        token_hash=token_hash,
        expires_at=expires_at,
    )

    db.add(invite)
    await db.commit()

    return InvitationResponse(token=plaintext_token)
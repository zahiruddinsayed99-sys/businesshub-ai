from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import RequiresPermission
from app.core.tenant_middleware import TenantContext, get_tenant_context
from app.repositories.tenant_repository import TenantRepository
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

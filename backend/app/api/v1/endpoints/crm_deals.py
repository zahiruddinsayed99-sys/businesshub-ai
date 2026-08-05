import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import RequiresPermission
from app.core.tenant_middleware import TenantContext, get_tenant_context
from app.repositories.crm_deal_repository import CrmDealRepository
from app.domain.models.crm_deal import CrmDeal
from app.schemas.crm_deal import CrmDealCreate, CrmDealUpdate, CrmDealUpdateStage, CrmDealResponse

router = APIRouter()

def get_crm_deal_repo(db: AsyncSession = Depends(get_db)) -> CrmDealRepository:
    return CrmDealRepository(db)

@router.get("", response_model=List[CrmDealResponse])
async def get_deals(
    context: TenantContext = Depends(RequiresPermission("crm:write")),
    repo: CrmDealRepository = Depends(get_crm_deal_repo)
):
    return await repo.get_all(context.organization_id)

@router.get("/{deal_id}", response_model=CrmDealResponse)
async def get_deal(
    deal_id: uuid.UUID,
    context: TenantContext = Depends(RequiresPermission("crm:write")),
    repo: CrmDealRepository = Depends(get_crm_deal_repo)
):
    return await repo.get_by_id(deal_id, context.organization_id)

@router.post("", response_model=CrmDealResponse, status_code=status.HTTP_201_CREATED)
async def create_deal(
    payload: CrmDealCreate,
    context: TenantContext = Depends(RequiresPermission("crm:write")),
    repo: CrmDealRepository = Depends(get_crm_deal_repo)
):
    deal = CrmDeal(
        organization_id=context.organization_id,
        **payload.model_dump(exclude_unset=True)
    )
    return await repo.create(deal)

@router.patch("/{deal_id}", response_model=CrmDealResponse)
async def update_deal(
    deal_id: uuid.UUID,
    payload: CrmDealUpdate,
    context: TenantContext = Depends(RequiresPermission("crm:write")),
    repo: CrmDealRepository = Depends(get_crm_deal_repo)
):
    return await repo.update_deal(
        deal_id=deal_id,
        update_data=payload.model_dump(exclude_unset=True),
        organization_id=context.organization_id,
        user_id=context.user_id,
        role=context.role
    )

@router.patch("/{deal_id}/stage", response_model=CrmDealResponse)
async def update_deal_stage(
    deal_id: uuid.UUID,
    payload: CrmDealUpdateStage,
    context: TenantContext = Depends(RequiresPermission("crm:write")),
    repo: CrmDealRepository = Depends(get_crm_deal_repo)
):
    return await repo.update_deal(
        deal_id=deal_id,
        update_data={"stage": payload.stage},
        organization_id=context.organization_id,
        user_id=context.user_id,
        role=context.role
    )

@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal(
    deal_id: uuid.UUID,
    context: TenantContext = Depends(RequiresPermission("crm:delete")),
    repo: CrmDealRepository = Depends(get_crm_deal_repo)
):
    await repo.delete(
        deal_id=deal_id,
        organization_id=context.organization_id,
        role=context.role
    )

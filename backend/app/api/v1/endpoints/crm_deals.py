import uuid
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from celery.result import AsyncResult
from app.core.celery_app import celery_app

from app.core.billing import check_soft_lock_overage, consume_ai_credits_br_plt_002, BillingError
from app.core.database import get_db
from app.core.rbac import RequiresPermission
from app.core.tenant_middleware import TenantContext, get_tenant_context
from app.repositories.crm_deal_repository import CrmDealRepository
from app.domain.models.crm_deal import CrmDeal
from app.schemas.crm_deal import (
    CrmDealCreate,
    CrmDealUpdate,
    CrmDealUpdateStage,
    CrmDealResponse,
)
from sqlalchemy import select
from app.tasks.crm_tasks import calculate_lead_score

router = APIRouter()


def get_crm_deal_repo(db: AsyncSession = Depends(get_db)) -> CrmDealRepository:
    return CrmDealRepository(db)


@router.get("", response_model=List[CrmDealResponse])
async def get_deals(
    context: TenantContext = Depends(RequiresPermission("crm:write")),
    repo: CrmDealRepository = Depends(get_crm_deal_repo),
):
    return await repo.get_all(context.organization_id)


@router.get("/{deal_id}", response_model=CrmDealResponse)
async def get_deal(
    deal_id: uuid.UUID,
    context: TenantContext = Depends(RequiresPermission("crm:write")),
    repo: CrmDealRepository = Depends(get_crm_deal_repo),
):
    return await repo.get_by_id(deal_id, context.organization_id)


@router.post("", response_model=CrmDealResponse, status_code=status.HTTP_201_CREATED)
async def create_deal(
    payload: CrmDealCreate,
    context: TenantContext = Depends(RequiresPermission("crm:write")),
    repo: CrmDealRepository = Depends(get_crm_deal_repo),
):
    await check_soft_lock_overage(repo.db, context.organization_id)
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
    repo: CrmDealRepository = Depends(get_crm_deal_repo),
):
    await check_soft_lock_overage(repo.db, context.organization_id)
    return await repo.update_deal(
        deal_id=deal_id,
        update_data=payload.model_dump(exclude_unset=True),
        organization_id=context.organization_id,
        user_id=context.user_id,
        role=context.role,
    )


@router.patch("/{deal_id}/stage", response_model=CrmDealResponse)
async def update_deal_stage(
    deal_id: uuid.UUID,
    payload: CrmDealUpdateStage,
    context: TenantContext = Depends(RequiresPermission("crm:write")),
    repo: CrmDealRepository = Depends(get_crm_deal_repo),
):
    await check_soft_lock_overage(repo.db, context.organization_id)
    return await repo.update_deal(
        deal_id=deal_id,
        update_data={"stage": payload.stage},
        organization_id=context.organization_id,
        user_id=context.user_id,
        role=context.role,
    )


@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal(
    deal_id: uuid.UUID,
    context: TenantContext = Depends(RequiresPermission("crm:delete")),
    repo: CrmDealRepository = Depends(get_crm_deal_repo),
):
    await check_soft_lock_overage(repo.db, context.organization_id)
    await repo.delete(
        deal_id=deal_id,
        organization_id=context.organization_id,
        role=context.role,
    )

@router.post("/{deal_id}/ai-score", status_code=status.HTTP_202_ACCEPTED)
async def score_deal_ai(
    deal_id: uuid.UUID,
    context: TenantContext = Depends(RequiresPermission("crm:write")),
    db: AsyncSession = Depends(get_db)
):
    # Verify deal exists and belongs to the org
    stmt = select(CrmDeal).where(CrmDeal.id == deal_id, CrmDeal.organization_id == context.organization_id)
    result = await db.execute(stmt)
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail={"code": "ERR_NOT_FOUND_001", "detail": "Deal not found"})

    await check_soft_lock_overage(db, context.organization_id)
    # Deduct 4 credits here. The background task executes a prompt consuming 1 more, making it 5 total.
    await consume_ai_credits_br_plt_002(db, context.organization_id, 4)

    # Needs a commit for ai_credits_used increment to take effect immediately
    await db.commit()

    job = calculate_lead_score.delay(str(deal_id))

    return {"job_id": job.id, "deal_id": str(deal_id)}

@router.post("/{deal_id}/draft-followup", status_code=status.HTTP_200_OK)
async def draft_deal_followup(
    deal_id: uuid.UUID,
    context: TenantContext = Depends(RequiresPermission("crm:write")),
    db: AsyncSession = Depends(get_db)
):
    # Verify deal exists and belongs to the org
    stmt = select(CrmDeal).where(CrmDeal.id == deal_id, CrmDeal.organization_id == context.organization_id)
    result = await db.execute(stmt)
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail={"code": "ERR_NOT_FOUND_001", "detail": "Deal not found"})

    await check_soft_lock_overage(db, context.organization_id)
    # Deduct 4 credits here. execute_prompt consumes 1 more, making it 5 total.
    await consume_ai_credits_br_plt_002(db, context.organization_id, 4)
    await db.commit()

    from app.domain.ai.gateway import AiGatewayService
    gateway = AiGatewayService(db)

    result = await gateway.execute_prompt(context.organization_id, "crm_followup_v1", {"deal_id": str(deal_id)})
    await db.commit()

    return {"draft": result}

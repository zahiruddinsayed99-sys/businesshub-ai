import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from app.domain.models.organization import Organization
from app.domain.models.user_role import UserRole

class BillingError(HTTPException):
    def __init__(self, detail: str = "Payment Required", code: str = "ERR_BILLING_001"):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"code": code, "detail": detail},
        )

async def consume_ai_credits_br_plt_002(
    db: AsyncSession, org_id: uuid.UUID, requested_credits: int
) -> uuid.UUID:
    stmt = text(
        """
        UPDATE organizations
        SET ai_credits_used = ai_credits_used + :requested_credits
        WHERE id = :org_id
        AND (
            subscription_tier = 'PRO'
            OR subscription_tier = 'ENTERPRISE'
            OR (ai_credits_used + :requested_credits <= 100 + bonus_ai_credits)
        )
        RETURNING id;
        """
    )
    result = await db.execute(
        stmt, {"org_id": org_id, "requested_credits": requested_credits}
    )
    updated_org_id = result.scalar()

    if not updated_org_id:
        raise BillingError(detail="Insufficient AI credits or subscription limit reached.", code="ERR_BILLING_001")

    return updated_org_id

async def check_soft_lock_overage(db: AsyncSession, org_id: uuid.UUID):
    stmt_org = select(Organization).where(Organization.id == org_id)
    org = (await db.execute(stmt_org)).scalars().first()

    if not org:
        return

    if org.subscription_tier == "FREE":
        stmt_users = select(func.count()).select_from(UserRole).where(UserRole.organization_id == org_id)
        user_count = (await db.execute(stmt_users)).scalar()

        if user_count > 3:
            raise BillingError(
                detail="Organization is soft-locked due to user overage on FREE tier.",
                code="ERR_BILLING_001"
            )

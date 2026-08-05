import uuid
from typing import List, Optional, Any, Dict
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.domain.models.crm_deal import CrmDeal

class CrmDealRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_deal_or_404(self, deal_id: uuid.UUID, organization_id: uuid.UUID) -> CrmDeal:
        stmt = select(CrmDeal).where(
            CrmDeal.id == deal_id,
            CrmDeal.organization_id == organization_id,
            CrmDeal.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        deal = result.scalars().first()
        if not deal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ERR_NOT_FOUND_001", "detail": "Deal not found"}
            )
        return deal

    async def get_by_id(self, deal_id: uuid.UUID, organization_id: uuid.UUID) -> CrmDeal:
        return await self._get_deal_or_404(deal_id, organization_id)

    async def get_all(self, organization_id: uuid.UUID) -> List[CrmDeal]:
        stmt = select(CrmDeal).where(
            CrmDeal.organization_id == organization_id,
            CrmDeal.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update_deal(
        self,
        deal_id: uuid.UUID,
        update_data: Dict[str, Any],
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str
    ) -> CrmDeal:
        deal = await self._get_deal_or_404(deal_id, organization_id)

        # Vertical Isolation: DOMAIN_MEMBER users can only modify deals where they are owner_user_id
        if role == "DOMAIN_MEMBER" and deal.owner_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "ERR_RBAC_001", "detail": "You do not have permission to modify this deal"}
            )

        for key, value in update_data.items():
            if hasattr(deal, key):
                setattr(deal, key, value)

        await self.db.flush()
        return deal

    async def delete(self, deal_id: uuid.UUID, organization_id: uuid.UUID, role: str) -> None:
        if role != "TENANT_OWNER":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "ERR_RBAC_001", "detail": "Only TENANT_OWNER can delete deals"}
            )

        deal = await self._get_deal_or_404(deal_id, organization_id)
        deal.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def create(self, deal: CrmDeal) -> CrmDeal:
        self.db.add(deal)
        await self.db.flush()
        return deal

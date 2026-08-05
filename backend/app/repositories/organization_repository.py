import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models.organization import Organization

class OrganizationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, organization: Organization) -> Organization:
        self.db.add(organization)
        # Flush is often necessary to get generated IDs within a transaction before commit
        await self.db.flush()
        return organization

    async def get_by_id(self, org_id: uuid.UUID) -> Optional[Organization]:
        stmt = select(Organization).where(Organization.id == org_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        stmt = select(Organization).where(Organization.slug == slug)
        result = await self.db.execute(stmt)
        return result.scalars().first()

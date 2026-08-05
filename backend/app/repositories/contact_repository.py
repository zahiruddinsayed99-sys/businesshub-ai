import uuid
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.domain.models.contact import Contact

class ContactRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, contact_id: uuid.UUID, organization_id: uuid.UUID) -> Contact:
        stmt = select(Contact).where(
            Contact.id == contact_id,
            Contact.organization_id == organization_id,
            Contact.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        contact = result.scalars().first()
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ERR_NOT_FOUND_001", "detail": "Contact not found"}
            )
        return contact

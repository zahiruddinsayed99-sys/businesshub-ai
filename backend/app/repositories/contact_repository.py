import uuid
from typing import List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.domain.models.contact import Contact

class ContactRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_contact_or_404(self, contact_id: uuid.UUID, organization_id: uuid.UUID) -> Contact:
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

    async def get_by_id(self, contact_id: uuid.UUID, organization_id: uuid.UUID) -> Contact:
        return await self._get_contact_or_404(contact_id, organization_id)

    async def get_all(self, organization_id: uuid.UUID) -> List[Contact]:
        stmt = select(Contact).where(
            Contact.organization_id == organization_id,
            Contact.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, contact: Contact) -> Contact:
        self.db.add(contact)
        await self.db.flush()
        return contact

    async def update(self, contact_id: uuid.UUID, update_data: Dict[str, Any], organization_id: uuid.UUID) -> Contact:
        contact = await self._get_contact_or_404(contact_id, organization_id)
        for key, value in update_data.items():
            if hasattr(contact, key):
                setattr(contact, key, value)
        await self.db.flush()
        return contact

    async def delete(self, contact_id: uuid.UUID, organization_id: uuid.UUID) -> None:
        contact = await self._get_contact_or_404(contact_id, organization_id)
        contact.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()

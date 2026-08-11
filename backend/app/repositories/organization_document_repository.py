import uuid
from typing import List, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models.organization_document import OrganizationDocument
import pgvector

class OrganizationDocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, document: OrganizationDocument) -> OrganizationDocument:
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def get_by_id(self, organization_id: uuid.UUID, document_id: uuid.UUID) -> Optional[OrganizationDocument]:
        stmt = select(OrganizationDocument).where(
            OrganizationDocument.id == document_id,
            OrganizationDocument.organization_id == organization_id,
            OrganizationDocument.deleted_at.is_(None)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def search_similar(self, organization_id: uuid.UUID, query_embedding: list[float], limit: int = 5) -> List[OrganizationDocument]:
        stmt = (
            select(OrganizationDocument)
            .where(
                OrganizationDocument.organization_id == organization_id,
                OrganizationDocument.deleted_at.is_(None)
            )
            .order_by(OrganizationDocument.embedding.l2_distance(query_embedding))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

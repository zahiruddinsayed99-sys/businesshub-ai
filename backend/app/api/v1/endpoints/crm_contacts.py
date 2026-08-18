import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import RequiresPermission
from app.core.tenant_middleware import TenantContext
from app.domain.models.contact import Contact
from app.repositories.contact_repository import ContactRepository
from app.schemas.contact import ContactCreate, ContactUpdate, ContactResponse

router = APIRouter()

def get_contact_repo(db: AsyncSession = Depends(get_db)) -> ContactRepository:
    return ContactRepository(db)

@router.get("", response_model=List[ContactResponse])
async def get_contacts(
    context: TenantContext = Depends(RequiresPermission("crm:read")),
    repo: ContactRepository = Depends(get_contact_repo),
):
    return await repo.get_all(context.organization_id)

@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: uuid.UUID,
    context: TenantContext = Depends(RequiresPermission("crm:read")),
    repo: ContactRepository = Depends(get_contact_repo),
):
    return await repo.get_by_id(contact_id, context.organization_id)

@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    payload: ContactCreate,
    context: TenantContext = Depends(RequiresPermission("crm:write")),
    repo: ContactRepository = Depends(get_contact_repo),
):
    contact = Contact(
        organization_id=context.organization_id,
        **payload.model_dump(exclude_unset=True)
    )
    return await repo.create(contact)

@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: uuid.UUID,
    payload: ContactUpdate,
    context: TenantContext = Depends(RequiresPermission("crm:write")),
    repo: ContactRepository = Depends(get_contact_repo),
):
    return await repo.update(
        contact_id=contact_id,
        update_data=payload.model_dump(exclude_unset=True),
        organization_id=context.organization_id,
    )

@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: uuid.UUID,
    context: TenantContext = Depends(RequiresPermission("crm:delete")),
    repo: ContactRepository = Depends(get_contact_repo),
):
    await repo.delete(contact_id, context.organization_id)

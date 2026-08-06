import uuid
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.tenant_middleware import TenantContext, get_tenant_context
from app.core.rbac import RequiresPermission
from pydantic import BaseModel
from app.tasks.ai_tasks import process_document_embeddings
from app.domain.models.organization_document import OrganizationDocument
from celery.result import AsyncResult
from app.core.celery_app import celery_app

router = APIRouter()

class DocumentUploadRequest(BaseModel):
    title: str
    content: str

@router.post("/documents/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    payload: DocumentUploadRequest,
    context: TenantContext = Depends(RequiresPermission("ai:write")),
    db: AsyncSession = Depends(get_db)
):
    document = OrganizationDocument(
        organization_id=context.organization_id,
        title=payload.title,
        content=payload.content
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    job = process_document_embeddings.delay(
        str(context.organization_id),
        str(document.id),
        payload.content
    )

    return {"job_id": job.id, "document_id": str(document.id)}

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, context: TenantContext = Depends(RequiresPermission("ai:read"))):
    job = AsyncResult(job_id, app=celery_app)

    return {
        "job_id": job_id,
        "status": job.status,
        "result": job.result if job.ready() else None
    }

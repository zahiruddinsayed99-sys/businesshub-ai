import uuid
from fastapi import APIRouter, Depends, status, Request, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.tenant_middleware import TenantContext, get_tenant_context
from app.core.rbac import RequiresPermission
from pydantic import BaseModel
from app.tasks.ai_tasks import process_document_embeddings
from app.domain.models.organization_document import OrganizationDocument
from app.domain.models.ai_job import AiJob
from sqlalchemy import select
from app.domain.ai.gateway import AiGatewayService

router = APIRouter()

class DocumentUploadRequest(BaseModel):
    title: str
    content: str

class ChatMessageRequest(BaseModel):
    message: str

@router.post("/chat", status_code=status.HTTP_200_OK)
async def chat_rag(
    payload: ChatMessageRequest,
    context: TenantContext = Depends(RequiresPermission("ai:read")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(OrganizationDocument).where(OrganizationDocument.organization_id == context.organization_id)
    documents = (await db.execute(stmt)).scalars().all()

    if not documents:
        return {"reply": "Please ingest a document first before chatting."}

    document_context = "\n\n".join([doc.content for doc in documents])

    gateway = AiGatewayService(db)

    try:
        reply = await gateway.execute_rag_chat(
            organization_id=context.organization_id,
            document_context=document_context,
            user_question=payload.message
        )
        return {"reply": reply}
    except Exception as e:
        return {"reply": f"Sorry, failed to get a response: {str(e)}"}

@router.post("/documents/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    payload: DocumentUploadRequest,
    background_tasks: BackgroundTasks,
    context: TenantContext = Depends(RequiresPermission("ai:write")),
    db: AsyncSession = Depends(get_db)
):
    document = OrganizationDocument(
        organization_id=context.organization_id,
        title=payload.title,
        content=payload.content
    )
    db.add(document)
    await db.flush()

    job = AiJob(
        organization_id=context.organization_id,
        status="PENDING"
    )
    db.add(job)
    await db.commit()
    await db.refresh(document)
    await db.refresh(job)

    background_tasks.add_task(
        process_document_embeddings,
        job.id,
        context.organization_id,
        document.id,
        payload.content
    )

    return {"job_id": str(job.id), "document_id": str(document.id)}

@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: uuid.UUID,
    context: TenantContext = Depends(RequiresPermission("ai:read")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AiJob).where(AiJob.id == job_id, AiJob.organization_id == context.organization_id)
    job = (await db.execute(stmt)).scalars().first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": str(job.id),
        "status": job.status,
        "result": job.result
    }

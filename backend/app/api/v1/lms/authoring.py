import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.tenant_middleware import get_tenant_context, TenantContext
from app.domain.lms.schemas import CourseCreate, CourseResponse, CourseModuleCreate, CourseModuleResponse, LessonCreate, LessonResponse, QuizGenerateRequest
from app.domain.lms import services

router = APIRouter()

# Helper dependency to enforce lms:write permissions
def require_lms_write(context: TenantContext = Depends(get_tenant_context)):
    # Allowed roles for lms:write scope
    if context.role not in ["TENANT_OWNER", "TENANT_ADMIN", "LMS_MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ERR_RBAC_001", "detail": "Insufficient permissions"}
        )
    return context

@router.post("/courses", response_model=CourseResponse)
async def create_course(
    course_in: CourseCreate,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(require_lms_write)
):
    return await services.create_course(db, context.organization_id, course_in)

@router.get("/courses/{id}", response_model=CourseResponse)
async def get_course(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(require_lms_write)
):
    return await services.get_course(db, id, context.organization_id)

@router.post("/courses/{id}/modules", response_model=CourseModuleResponse)
async def create_module(
    id: uuid.UUID,
    module_in: CourseModuleCreate,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(require_lms_write)
):
    return await services.add_module(db, id, context.organization_id, module_in)

@router.post("/modules/{id}/lessons", response_model=LessonResponse)
async def create_lesson(
    id: uuid.UUID, # this is the module ID
    lesson_in: LessonCreate,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(require_lms_write)
):
    return await services.add_lesson(db, id, context.organization_id, lesson_in)

@router.patch("/courses/{id}/status", response_model=CourseResponse)
async def publish_course(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(require_lms_write)
):
    return await services.publish_course(db, id, context.organization_id)

@router.post("/quizzes/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_quiz(
    request: QuizGenerateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(require_lms_write)
):
    from app.core.billing import check_soft_lock_overage, consume_ai_credits_br_plt_002

    # 1. Verify organization is not in Soft-Lock Overage state
    await check_soft_lock_overage(db, context.organization_id)

    # 2. Pre-flight Billing Guard (BR-PLT-002) - Deduct 10 AI credits
    await consume_ai_credits_br_plt_002(db, context.organization_id, 10)

    # 3. Dispatch Background Celery Worker
    from app.tasks.ai_tasks import generate_ai_quiz
    task = generate_ai_quiz.delay(
        str(context.organization_id),
        request.lesson_id
    )

    return {"status": "accepted", "job_id": task.id}

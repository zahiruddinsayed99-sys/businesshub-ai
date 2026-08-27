import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.tenant_middleware import get_tenant_context, TenantContext
from app.domain.lms.learner_schemas import EnrollmentCreate, EnrollmentResponse, ProgressUpdate, ProgressResponse, QuizSubmission, QuizResult
from app.domain.lms import learner_services

router = APIRouter()

def require_lms_read(context: TenantContext = Depends(get_tenant_context)):
    if not context.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ERR_RBAC_001", "detail": "Insufficient permissions"}
        )
    return context

@router.get("/courses", response_model=list[dict])
async def get_published_courses(
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(require_lms_read)
):
    from sqlalchemy import select, and_
    from app.domain.models.lms import Course
    stmt = select(Course).where(
        and_(
            Course.organization_id == context.organization_id,
            Course.status == 'PUBLISHED'
        )
    )
    result = await db.execute(stmt)
    courses = result.scalars().all()
    return [{"id": str(c.id), "title": c.title, "description": c.description} for c in courses]



@router.post("/enrollments", response_model=EnrollmentResponse)
async def enroll_course(
    enroll_in: EnrollmentCreate,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(require_lms_read)
):
    return await learner_services.enroll_user(
        db, context.organization_id, context.user_id, enroll_in.course_id
    )

@router.post("/lessons/{id}/progress", response_model=ProgressResponse)
async def log_progress(
    id: uuid.UUID,
    progress_in: ProgressUpdate,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(require_lms_read)
):
    return await learner_services.update_lesson_progress(
        db, context.organization_id, context.user_id, id, progress_in.is_completed
    )

@router.post("/quizzes/attempts", response_model=QuizResult)
async def submit_quiz(
    quiz_id: uuid.UUID,
    submission: QuizSubmission,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(require_lms_read)
):
    attempt = await learner_services.submit_quiz_attempt(
        db, context.organization_id, context.user_id, quiz_id, submission.responses
    )
    return QuizResult(
        attempt_id=attempt.id,
        score=attempt.score,
        passed=attempt.passed
    )

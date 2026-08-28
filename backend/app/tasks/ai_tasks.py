import uuid
import asyncio
import logging

from app.core.redis import get_redis_client, close_redis_client
from app.core.database import get_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from app.domain.ai.gateway import AiGatewayService
from app.domain.models.organization_document import OrganizationDocument
from app.domain.models.ai_job import AiJob
import time

logger = logging.getLogger(__name__)

async def process_document_embeddings(job_id: uuid.UUID, organization_id: uuid.UUID, document_id: uuid.UUID, text_content: str):
    redis = await get_redis_client()
    lock_key = f"ai_lock:doc:{str(document_id)}"

    acquired = await redis.set(lock_key, "1", nx=True, ex=300)
    if not acquired:
        return {"status": "duplicate_run", "document_id": str(document_id)}

    try:
        engine = get_engine()
        SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
        async with SessionLocal() as db:
            gateway = AiGatewayService(db)

            try:
                embeddings = await gateway.generate_embeddings(organization_id, text_content)

                from sqlalchemy import update

                # Update Document
                stmt = update(OrganizationDocument).where(
                    OrganizationDocument.id == document_id,
                    OrganizationDocument.organization_id == organization_id
                ).values(embedding=embeddings)
                await db.execute(stmt)

                # Update Job status
                job_stmt = update(AiJob).where(
                    AiJob.id == job_id
                ).values(status="SUCCESS", result={"status": "completed", "document_id": str(document_id)})
                await db.execute(job_stmt)

                await db.commit()

            except Exception as e:
                # Update Job status to failure
                job_stmt = update(AiJob).where(
                    AiJob.id == job_id
                ).values(status="FAILURE", result={"detail": str(e)})
                await db.execute(job_stmt)
                await db.commit()
                raise e

        return {"status": "completed", "document_id": str(document_id)}
    finally:
        await redis.delete(lock_key)

async def generate_ai_quiz(job_id: uuid.UUID | None, organization_id: uuid.UUID, lesson_id: uuid.UUID):
    redis = await get_redis_client()
    lock_key = f"ai_lock:quiz_gen:{str(lesson_id)}"

    acquired = await redis.set(lock_key, "1", nx=True, ex=300)
    if not acquired:
        return {"status": "duplicate_run", "lesson_id": str(lesson_id)}

    try:
        engine = get_engine()
        SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
        async with SessionLocal() as db:
            from sqlalchemy import select, and_
            from app.domain.models.lms import Lesson, Quiz, QuizQuestion, QuizAnswer

            # Query the lesson's Markdown text content
            stmt = select(Lesson).where(
                and_(Lesson.id == lesson_id, Lesson.organization_id == organization_id)
            )
            lesson = (await db.execute(stmt)).scalars().first()
            if not lesson:
                return {"status": "error", "detail": "Lesson not found"}

            gateway = AiGatewayService(db)

            try:
                quiz_data = await gateway.generate_quiz(organization_id, lesson.content_body or "")

                # Save resulting questions, answers, and keys atomically
                quiz = Quiz(
                    organization_id=organization_id,
                    lesson_id=lesson_id,
                    title=quiz_data.get("title", f"Quiz for Lesson {lesson.title}")
                )
                db.add(quiz)
                await db.flush()

                for q_data in quiz_data.get("questions", []):
                    question = QuizQuestion(
                        quiz_id=quiz.id,
                        question_text=q_data["question_text"]
                    )
                    db.add(question)
                    await db.flush()

                    for a_data in q_data.get("answers", []):
                        answer = QuizAnswer(
                            question_id=question.id,
                            answer_text=a_data["answer_text"],
                            is_correct=a_data["is_correct"]
                        )
                        db.add(answer)

                if job_id:
                    from sqlalchemy import update
                    job_stmt = update(AiJob).where(AiJob.id == job_id).values(
                        status="SUCCESS",
                        result={"status": "completed", "lesson_id": str(lesson_id)}
                    )
                    await db.execute(job_stmt)

                await db.commit()

            except Exception as e:
                logger.error(f"Error generating AI quiz for lesson {lesson_id}: {e}", exc_info=True)
                if job_id:
                    from sqlalchemy import update
                    job_stmt = update(AiJob).where(AiJob.id == job_id).values(
                        status="FAILURE",
                        result={"detail": str(e)}
                    )
                    await db.execute(job_stmt)
                    await db.commit()
                raise e

        return {"status": "completed", "lesson_id": str(lesson_id)}
    finally:
        await redis.delete(lock_key)

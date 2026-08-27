import uuid
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status
from datetime import datetime, timezone

from app.domain.models.lms import CourseEnrollment, LessonProgress, Course, Lesson, CourseModule, Quiz, QuizQuestion, QuizAnswer, QuizAttempt, QuizResponse

async def get_available_courses(session: AsyncSession, organization_id: uuid.UUID):
    stmt = select(Course).where(and_(Course.organization_id == organization_id, Course.status == "PUBLISHED", Course.deleted_at.is_(None)))
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def get_user_enrollments(session: AsyncSession, organization_id: uuid.UUID, user_id: uuid.UUID):
    stmt = select(CourseEnrollment).where(and_(CourseEnrollment.organization_id == organization_id, CourseEnrollment.user_id == user_id, CourseEnrollment.deleted_at.is_(None)))
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def get_lesson_quiz(session: AsyncSession, organization_id: uuid.UUID, lesson_id: uuid.UUID):
    from sqlalchemy.orm import selectinload
    stmt = select(Quiz).options(
        selectinload(Quiz.questions).selectinload(QuizQuestion.answers)
    ).where(and_(Quiz.lesson_id == lesson_id, Quiz.organization_id == organization_id))
    result = await session.execute(stmt)
    return result.scalars().first()

async def get_enrolled_course_detail(session: AsyncSession, organization_id: uuid.UUID, user_id: uuid.UUID, course_id: uuid.UUID):
    from sqlalchemy.orm import selectinload

    stmt_enroll = select(CourseEnrollment).where(and_(CourseEnrollment.user_id == user_id, CourseEnrollment.course_id == course_id, CourseEnrollment.organization_id == organization_id))
    result_enroll = await session.execute(stmt_enroll)
    if not result_enroll.scalars().first():
        raise HTTPException(status_code=403, detail="Not enrolled in this course")

    stmt = select(Course).options(
        selectinload(Course.modules).selectinload(CourseModule.lessons)
    ).where(
        and_(
            Course.id == course_id,
            Course.organization_id == organization_id,
            Course.deleted_at.is_(None)
        )
    )
    result = await session.execute(stmt)
    course = result.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return course

async def get_user_lesson_progresses(session: AsyncSession, organization_id: uuid.UUID, user_id: uuid.UUID, course_id: uuid.UUID):
    stmt_enroll = select(CourseEnrollment).where(and_(CourseEnrollment.user_id == user_id, CourseEnrollment.course_id == course_id, CourseEnrollment.organization_id == organization_id))
    result_enroll = await session.execute(stmt_enroll)
    enrollment = result_enroll.scalars().first()
    if not enrollment:
        return []

    stmt = select(LessonProgress).where(LessonProgress.enrollment_id == enrollment.id)
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def enroll_user(
    session: AsyncSession, organization_id: uuid.UUID, user_id: uuid.UUID, course_id: uuid.UUID
) -> CourseEnrollment:
    # Validate course exists in org
    stmt = select(Course).where(and_(Course.id == course_id, Course.organization_id == organization_id))
    result = await session.execute(stmt)
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail={"code": "ERR_NOT_FOUND_001", "detail": "Course not found"})

    enrollment = CourseEnrollment(
        organization_id=organization_id,
        user_id=user_id,
        course_id=course_id
    )
    session.add(enrollment)
    await session.commit()
    await session.refresh(enrollment)
    return enrollment

async def update_lesson_progress(
    session: AsyncSession, organization_id: uuid.UUID, user_id: uuid.UUID, lesson_id: uuid.UUID, is_completed: bool
):
    # Get enrollment
    stmt = select(CourseEnrollment).join(Course).join(CourseModule).join(Lesson).where(
        and_(
            CourseEnrollment.user_id == user_id,
            CourseEnrollment.organization_id == organization_id,
            Lesson.id == lesson_id
        )
    )
    result = await session.execute(stmt)
    enrollment = result.scalars().first()

    if not enrollment:
        raise HTTPException(status_code=404, detail={"code": "ERR_NOT_FOUND_001", "detail": "Enrollment not found"})

    # Upsert progress
    stmt = select(LessonProgress).where(
        and_(
            LessonProgress.enrollment_id == enrollment.id,
            LessonProgress.lesson_id == lesson_id
        )
    )
    result = await session.execute(stmt)
    progress = result.scalars().first()

    if progress:
        progress.is_completed = is_completed
        if is_completed and not progress.completed_at:
            progress.completed_at = datetime.now(timezone.utc)
    else:
        progress = LessonProgress(
            organization_id=organization_id,
            enrollment_id=enrollment.id,
            lesson_id=lesson_id,
            is_completed=is_completed,
            completed_at=datetime.now(timezone.utc) if is_completed else None
        )
        session.add(progress)

    await session.commit()
    await session.refresh(progress)

    # Check if all lessons are completed
    if is_completed:
        # Get all lessons for course
        all_lessons_stmt = select(Lesson.id).join(CourseModule).where(CourseModule.course_id == enrollment.course_id)
        all_lessons = (await session.execute(all_lessons_stmt)).scalars().all()

        # Get completed lessons for enrollment
        completed_lessons_stmt = select(LessonProgress.lesson_id).where(
            and_(
                LessonProgress.enrollment_id == enrollment.id,
                LessonProgress.is_completed == True
            )
        )
        completed_lessons = (await session.execute(completed_lessons_stmt)).scalars().all()

        if set(all_lessons).issubset(set(completed_lessons)):
            enrollment.status = "COMPLETED"
            enrollment.completed_at = datetime.now(timezone.utc)
            session.add(enrollment)
            await session.commit()

    return progress

async def submit_quiz_attempt(
    session: AsyncSession, organization_id: uuid.UUID, user_id: uuid.UUID, quiz_id: uuid.UUID, responses: Dict[uuid.UUID, uuid.UUID]
) -> QuizAttempt:
    # 1. Fetch quiz and validate org
    stmt = select(Quiz).where(and_(Quiz.id == quiz_id, Quiz.organization_id == organization_id))
    result = await session.execute(stmt)
    quiz = result.scalars().first()

    if not quiz:
        raise HTTPException(status_code=404, detail={"code": "ERR_NOT_FOUND_001", "detail": "Quiz not found"})

    # 2. Fetch all questions and their correct answers
    q_stmt = select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id)
    questions = (await session.execute(q_stmt)).scalars().all()

    if not questions:
        raise HTTPException(status_code=400, detail="Quiz has no questions")

    correct_answers_count = 0
    total_questions = len(questions)

    # Track responses for insertion
    attempt_responses = []

    for q in questions:
        a_stmt = select(QuizAnswer).where(
            and_(QuizAnswer.question_id == q.id, QuizAnswer.is_correct == True)
        )
        correct_answer = (await session.execute(a_stmt)).scalars().first()

        selected_answer_id = responses.get(q.id)
        if selected_answer_id and correct_answer and selected_answer_id == correct_answer.id:
            correct_answers_count += 1

        if selected_answer_id:
            attempt_responses.append(QuizResponse(
                question_id=q.id,
                selected_answer_id=selected_answer_id
            ))

    score = (correct_answers_count / total_questions) * 100
    passed = score >= 80.0

    attempt = QuizAttempt(
        organization_id=organization_id,
        user_id=user_id,
        quiz_id=quiz_id,
        score=score,
        passed=passed
    )
    session.add(attempt)
    await session.flush()

    for resp in attempt_responses:
        resp.attempt_id = attempt.id
        session.add(resp)

    await session.commit()
    await session.refresh(attempt)

    return attempt

import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.domain.models.lms import Course, CourseModule, Lesson
from app.domain.lms.repositories import CourseRepository, LessonRepository
from app.domain.lms.schemas import CourseCreate, CourseModuleCreate, LessonCreate

async def create_course(
    session: AsyncSession, organization_id: uuid.UUID, course_in: CourseCreate
) -> Course:
    repo = CourseRepository(session)
    course = Course(
        organization_id=organization_id,
        title=course_in.title,
        description=course_in.description,
        status="DRAFT"
    )
    return await repo.create(course)

async def list_courses(session: AsyncSession, organization_id: uuid.UUID) -> List[Course]:
    repo = CourseRepository(session)
    return await repo.list_courses(organization_id)

async def get_course_detail(session: AsyncSession, course_id: uuid.UUID, organization_id: uuid.UUID) -> Course:
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select, and_

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ERR_NOT_FOUND_001", "detail": "Course not found"}
        )
    return course

async def get_course(
    session: AsyncSession, course_id: uuid.UUID, organization_id: uuid.UUID
) -> Course:
    repo = CourseRepository(session)
    course = await repo.get_by_id(course_id, organization_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ERR_NOT_FOUND_001", "detail": "Course not found"}
        )
    return course

async def publish_course(
    session: AsyncSession, course_id: uuid.UUID, organization_id: uuid.UUID
) -> Course:
    repo = CourseRepository(session)
    course = await repo.get_by_id(course_id, organization_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ERR_NOT_FOUND_001", "detail": "Course not found"}
        )
    course.status = "PUBLISHED"
    return await repo.update(course)

async def add_module(
    session: AsyncSession, course_id: uuid.UUID, organization_id: uuid.UUID, module_in: CourseModuleCreate
) -> CourseModule:
    # Verify course exists and belongs to organization
    await get_course(session, course_id, organization_id)

    module = CourseModule(
        organization_id=organization_id,
        course_id=course_id,
        title=module_in.title,
        sort_order=module_in.sort_order
    )
    session.add(module)
    await session.commit()
    await session.refresh(module)
    return module

async def add_lesson(
    session: AsyncSession, module_id: uuid.UUID, organization_id: uuid.UUID, lesson_in: LessonCreate
) -> Lesson:
    # Need to verify module exists and belongs to the correct org
    from sqlalchemy import select, and_

    stmt = select(CourseModule).where(
        and_(
            CourseModule.id == module_id,
            CourseModule.organization_id == organization_id
        )
    )
    result = await session.execute(stmt)
    module = result.scalars().first()

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ERR_NOT_FOUND_001", "detail": "Module not found"}
        )

    lesson = Lesson(
        organization_id=organization_id,
        module_id=module_id,
        title=lesson_in.title,
        content_body=lesson_in.content_body,
        video_url=lesson_in.video_url,
        sort_order=lesson_in.sort_order
    )
    repo = LessonRepository(session)
    return await repo.create(lesson)

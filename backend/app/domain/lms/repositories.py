from typing import List, Optional
import uuid
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models.lms import Course, CourseModule, Lesson, CourseEnrollment, LessonProgress

class BaseLmsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

class CourseRepository(BaseLmsRepository):
    async def get_by_id(self, course_id: uuid.UUID, organization_id: uuid.UUID) -> Optional[Course]:
        stmt = select(Course).where(
            and_(
                Course.id == course_id,
                Course.organization_id == organization_id,
                Course.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_courses(self, organization_id: uuid.UUID) -> List[Course]:
        stmt = select(Course).where(
            and_(
                Course.organization_id == organization_id,
                Course.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, course: Course) -> Course:
        self.session.add(course)
        await self.session.commit()
        await self.session.refresh(course)
        return course

    async def update(self, course: Course) -> Course:
        self.session.add(course)
        await self.session.commit()
        await self.session.refresh(course)
        return course

class LessonRepository(BaseLmsRepository):
    async def get_by_id(self, lesson_id: uuid.UUID, organization_id: uuid.UUID) -> Optional[Lesson]:
        stmt = select(Lesson).where(
            and_(
                Lesson.id == lesson_id,
                Lesson.organization_id == organization_id,
                Lesson.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, lesson: Lesson) -> Lesson:
        self.session.add(lesson)
        await self.session.commit()
        await self.session.refresh(lesson)
        return lesson

class EnrollmentRepository(BaseLmsRepository):
    async def get_enrollment(self, user_id: uuid.UUID, course_id: uuid.UUID, organization_id: uuid.UUID) -> Optional[CourseEnrollment]:
        stmt = select(CourseEnrollment).where(
            and_(
                CourseEnrollment.user_id == user_id,
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.organization_id == organization_id,
                CourseEnrollment.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, enrollment: CourseEnrollment) -> CourseEnrollment:
        self.session.add(enrollment)
        await self.session.commit()
        await self.session.refresh(enrollment)
        return enrollment

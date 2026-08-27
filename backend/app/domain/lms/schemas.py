from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
import uuid
from datetime import datetime

class CourseBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class CourseResponse(CourseBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CourseModuleCreate(BaseModel):
    title: str = Field(..., max_length=255)
    sort_order: int = 0

class CourseModuleResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    title: str
    sort_order: int
    model_config = ConfigDict(from_attributes=True)

class LessonCreate(BaseModel):
    title: str = Field(..., max_length=255)
    content_body: Optional[str] = None
    video_url: Optional[str] = None
    sort_order: int = 0

class LessonResponse(BaseModel):
    id: uuid.UUID
    module_id: uuid.UUID
    title: str
    content_body: Optional[str] = None
    video_url: Optional[str] = None
    sort_order: int
    model_config = ConfigDict(from_attributes=True)

class QuizGenerateRequest(BaseModel):
    lesson_id: str

class QuizAnswerResponse(BaseModel):
    id: uuid.UUID
    answer_text: str
    model_config = ConfigDict(from_attributes=True)

class QuizQuestionResponse(BaseModel):
    id: uuid.UUID
    question_text: str
    answers: List[QuizAnswerResponse]
    model_config = ConfigDict(from_attributes=True)

class QuizResponseModel(BaseModel):
    id: uuid.UUID
    title: str
    questions: List[QuizQuestionResponse]
    model_config = ConfigDict(from_attributes=True)

class CourseModuleDetail(CourseModuleResponse):
    lessons: List[LessonResponse] = []
    model_config = ConfigDict(from_attributes=True)

class CourseDetailResponse(CourseResponse):
    modules: List[CourseModuleDetail] = []
    model_config = ConfigDict(from_attributes=True)

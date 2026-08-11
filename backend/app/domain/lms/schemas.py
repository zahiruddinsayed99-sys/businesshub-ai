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

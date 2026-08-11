from pydantic import BaseModel
import uuid
from typing import List, Dict

class EnrollmentCreate(BaseModel):
    course_id: uuid.UUID

class EnrollmentResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    status: str

class ProgressUpdate(BaseModel):
    is_completed: bool

class ProgressResponse(BaseModel):
    id: uuid.UUID
    lesson_id: uuid.UUID
    is_completed: bool

class QuizSubmission(BaseModel):
    responses: Dict[uuid.UUID, uuid.UUID]  # Map of question_id -> selected_answer_id

class QuizResult(BaseModel):
    attempt_id: uuid.UUID
    score: float
    passed: bool

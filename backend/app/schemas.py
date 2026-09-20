from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SemesterCreate(BaseModel):
    name: str


class SemesterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    created_at: datetime


class CourseCreate(BaseModel):
    name: str
    code: str | None = None


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    semester_id: int
    name: str
    code: str | None
    created_at: datetime


class SyllabusUploadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    course_id: int
    original_filename: str
    content_type: str | None
    size_bytes: int
    status: str
    uploaded_at: datetime

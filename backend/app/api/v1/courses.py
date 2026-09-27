from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.course import CourseResponse
from app.services import course_service

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("/upload-syllabus", response_model=CourseResponse, response_model_by_alias=True)
async def upload_syllabus(
    pdfFile: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    pdf_bytes = await pdfFile.read()
    course = course_service.create_course_from_syllabus(db, user.id, pdf_bytes)
    return course_service.course_to_response(course)


@router.get("/", response_model=list[CourseResponse], response_model_by_alias=True)
def get_courses(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    courses = course_service.list_courses(db, user.id)
    return [course_service.course_to_response(c) for c in courses]


@router.get("/{course_id}", response_model=CourseResponse, response_model_by_alias=True)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = course_service.get_course(db, user.id, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course_service.course_to_response(course)

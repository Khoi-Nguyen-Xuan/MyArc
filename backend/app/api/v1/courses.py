import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.course import CourseResponse
from app.services import course_service
from app.services.course_analysis import AnalysisError, SetupError
from app.utils.documents import DocumentError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("/upload-syllabus", response_model=CourseResponse, response_model_by_alias=True)
async def upload_syllabus(
    pdfFile: UploadFile = File(..., description="The syllabus, as a PDF or .docx"),
    course_code: str | None = Form(None, description='e.g. "CMPUT 201"; read from the syllabus when empty'),
    term: str | None = Form(None, description='e.g. "Fall 2026"'),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Analyze a syllabus with the agents and save it as a course. Takes a few minutes."""
    file_bytes = await pdfFile.read()
    try:
        course = await course_service.create_course_from_syllabus(
            db,
            user.id,
            file_bytes,
            pdfFile.filename or "syllabus",
            course_code=course_code or None,
            term=term or None,
        )
    except (DocumentError, AnalysisError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except SetupError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Syllabus analysis failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The analysis failed. Please try again in a minute.",
        ) from exc
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

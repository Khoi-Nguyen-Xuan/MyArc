from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Course, Semester
from app.schemas import CourseCreate, CourseOut

router = APIRouter(prefix="/api", tags=["courses"])


@router.post("/semesters/{semester_id}/courses", response_model=CourseOut)
def create_course(semester_id: int, payload: CourseCreate, db: Session = Depends(get_db)):
    semester = db.get(Semester, semester_id)
    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found")
    course = Course(semester_id=semester_id, name=payload.name, code=payload.code)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.get("/semesters/{semester_id}/courses", response_model=list[CourseOut])
def list_courses(semester_id: int, db: Session = Depends(get_db)):
    return db.scalars(
        select(Course).where(Course.semester_id == semester_id).order_by(Course.created_at)
    ).all()

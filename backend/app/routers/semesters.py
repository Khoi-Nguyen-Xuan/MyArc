from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Semester
from app.schemas import SemesterCreate, SemesterOut

router = APIRouter(prefix="/api/semesters", tags=["semesters"])


@router.post("", response_model=SemesterOut)
def create_semester(payload: SemesterCreate, db: Session = Depends(get_db)):
    semester = Semester(name=payload.name)
    db.add(semester)
    db.commit()
    db.refresh(semester)
    return semester


@router.get("", response_model=list[SemesterOut])
def list_semesters(db: Session = Depends(get_db)):
    return db.scalars(select(Semester).order_by(Semester.created_at.desc())).all()


@router.get("/{semester_id}", response_model=SemesterOut)
def get_semester(semester_id: int, db: Session = Depends(get_db)):
    semester = db.get(Semester, semester_id)
    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found")
    return semester

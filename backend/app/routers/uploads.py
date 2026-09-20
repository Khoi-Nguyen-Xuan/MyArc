import os
import shutil
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Course, SyllabusUpload
from app.schemas import SyllabusUploadOut

router = APIRouter(prefix="/api", tags=["uploads"])

STORAGE_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage")
ALLOWED_CONTENT_TYPES = {"application/pdf"}


@router.post("/courses/{course_id}/uploads", response_model=SyllabusUploadOut)
def upload_syllabus(course_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files are accepted right now")

    course_dir = os.path.join(STORAGE_ROOT, str(course_id))
    os.makedirs(course_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    safe_name = file.filename.replace("/", "_").replace("\\", "_")
    stored_name = f"{timestamp}__{safe_name}"
    stored_path = os.path.join(course_dir, stored_name)

    with open(stored_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    size_bytes = os.path.getsize(stored_path)

    record = SyllabusUpload(
        course_id=course_id,
        original_filename=file.filename,
        stored_path=stored_path,
        content_type=file.content_type,
        size_bytes=size_bytes,
        status="uploaded",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/courses/{course_id}/uploads", response_model=list[SyllabusUploadOut])
def list_course_uploads(course_id: int, db: Session = Depends(get_db)):
    return db.scalars(
        select(SyllabusUpload)
        .where(SyllabusUpload.course_id == course_id)
        .order_by(SyllabusUpload.uploaded_at.desc())
    ).all()


@router.get("/uploads", response_model=list[SyllabusUploadOut])
def list_all_uploads(db: Session = Depends(get_db)):
    """Global history trail across every course -- powers an activity feed."""
    return db.scalars(select(SyllabusUpload).order_by(SyllabusUpload.uploaded_at.desc())).all()

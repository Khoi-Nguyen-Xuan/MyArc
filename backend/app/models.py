
from datetime import datetime, timezone

from sqlalchemy import String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Semester(Base):
    __tablename__ = "semesters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    courses: Mapped[list["Course"]] = relationship(
        back_populates="semester", cascade="all, delete-orphan"
    )


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"))
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    semester: Mapped["Semester"] = relationship(back_populates="courses")
    uploads: Mapped[list["SyllabusUpload"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )


class SyllabusUpload(Base):
    """One row per uploaded file"""
    __tablename__ = "syllabus_uploads"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="uploaded")
    # status will move through: uploaded -> parsing -> parsed -> failed
    # once the ingestion/RAG pipeline lands in a later milestone.
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    course: Mapped["Course"] = relationship(back_populates="uploads")

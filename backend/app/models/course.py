from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.db.base_class import Base


class Course(Base):
    __tablename__ = "course"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    course_semester = Column(String)
    course_name = Column(String)
    professor_name = Column(String)
    course_code = Column(String)

    # [{id, type: assessment|midterm|quiz, score_percent (sums to 1 across
    #   the array — validated at the API layer, not the DB), date: "YYYY-MM-DD"}]
    assessments = Column(JSONB)
    # [{id, link, content_summary}]
    evidence = Column(JSONB)

    short_review = Column(Text)
    workload = Column(Float)
    conceptual_difficulty = Column(Float)
    assessment_weighting = Column(Float)
    continious_study_requirement = Column(Float)
    student_review = Column(Float)

    summary = Column(Text)
    reasoning = Column(Text)
    ranking = Column(String)
    point = Column(Float)
    confidence = Column(Float)

    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())

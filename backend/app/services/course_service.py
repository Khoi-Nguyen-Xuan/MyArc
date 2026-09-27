from sqlalchemy.orm import Session

from app.models.course import Course
from app.schemas.course import CourseResponse
from app.utils.pdf_parser import extract_text_from_pdf


def _run_placeholder_analysis(syllabus_text: str) -> dict:
    """STUB — replace with the real multi-agent pipeline
    (app/agents/orchestrator.py: parser -> research -> evaluator -> critic).

    Returns zeroed/empty analysis so the upload -> save -> retrieve flow is
    fully testable before the LLM pipeline (which needs an API key) exists.
    """
    preview = syllabus_text.strip().replace("\n", " ")[:300]
    return {
        "course_semester": None,
        "course_name": None,
        "professor_name": None,
        "course_code": None,
        "assessments": [],
        "short_review": None,
        "workload": 0.0,
        "conceptual_difficulty": 0.0,
        "assessment_weighting": 0.0,
        "continious_study_requirement": 0.0,
        "student_review": 0.0,
        "evidence": [],
        "summary": f"[placeholder] PDF text extracted ({len(syllabus_text)} chars). "
        f"Preview: {preview}...",
        "reasoning": "[placeholder] Real analysis pipeline not wired up yet.",
        "ranking": None,
        "point": 0.0,
        "confidence": 0.0,
    }


def create_course_from_syllabus(db: Session, user_id: int, pdf_bytes: bytes) -> Course:
    text = extract_text_from_pdf(pdf_bytes)
    analysis = _run_placeholder_analysis(text)

    course = Course(user_id=user_id, **analysis)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def list_courses(db: Session, user_id: int) -> list[Course]:
    return (
        db.query(Course)
        .filter(Course.user_id == user_id)
        .order_by(Course.created_at.desc())
        .all()
    )


def get_course(db: Session, user_id: int, course_id: int) -> Course | None:
    return (
        db.query(Course)
        .filter(Course.id == course_id, Course.user_id == user_id)
        .first()
    )


def course_to_response(course: Course) -> CourseResponse:
    return CourseResponse(
        id=course.id,
        course_semester=course.course_semester,
        course_name=course.course_name,
        professor_name=course.professor_name,
        course_code=course.course_code,
        evaluate=course.assessments or [],
        short_review=course.short_review,
        workload=course.workload,
        conceptual_difficulty=course.conceptual_difficulty,
        assessment_weighting=course.assessment_weighting,
        continious_study_requirement=course.continious_study_requirement,
        student_review=course.student_review,
        evidence=course.evidence or [],
        summary=course.summary,
        reasoning=course.reasoning,
        ranking=course.ranking,
        point=course.point,
        confidence=course.confidence,
    )

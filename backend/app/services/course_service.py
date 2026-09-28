from sqlalchemy.orm import Session

from app.agents.evaluator.schemas import Criterion, CourseEvaluation
from app.agents.syllabus.schemas import SyllabusResult
from app.core.course_codes import normalize_course_code, normalize_course_title
from app.models.course import Course
from app.schemas.course import CourseResponse
from app.services.course_analysis import CourseAnalysis, analyze_syllabus

CRITERION_LABELS = {
    Criterion.WORKLOAD: "Workload",
    Criterion.CONCEPTUAL_DIFFICULTY: "Conceptual difficulty",
    Criterion.DEADLINE_PRESSURE: "Deadline pressure",
    Criterion.ASSESSMENT_WEIGHTING: "Assessment weighting",
    Criterion.CONTINUOUS_STUDY: "Continuous-study requirement",
    Criterion.STUDENT_REVIEW_DIFFICULTY: "Student-review difficulty",
}


async def create_course_from_syllabus(
    db: Session,
    user_id: int,
    file_bytes: bytes,
    file_name: str,
    *,
    course_code: str | None = None,
    term: str | None = None,
) -> Course:
    """Run the agents on the syllabus, then save the result as a course."""
    analysis = await analyze_syllabus(file_bytes, file_name, course_code=course_code, term=term)
    course = Course(user_id=user_id, **_to_columns(analysis))
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def _to_columns(analysis: CourseAnalysis) -> dict:
    """Agent results -> course columns. Scores, point and confidence are stored out of 10."""
    syllabus, evaluation = analysis.syllabus, analysis.evaluation
    return {
        "course_semester": syllabus.term or syllabus.request.term,
        "course_name": normalize_course_title(syllabus.course_title) if syllabus.course_title else None,
        "professor_name": ", ".join(syllabus.instructors) or None,
        "course_code": normalize_course_code(evaluation.course_code) if evaluation.course_code else None,
        "assessments": _assessments(syllabus),
        "evidence": _evidence(evaluation),
        "short_review": evaluation.short_review,
        "workload": _out_of_10(evaluation.score(Criterion.WORKLOAD)),
        "conceptual_difficulty": _out_of_10(evaluation.score(Criterion.CONCEPTUAL_DIFFICULTY)),
        "assessment_weighting": _out_of_10(evaluation.score(Criterion.ASSESSMENT_WEIGHTING)),
        "continious_study_requirement": _out_of_10(evaluation.score(Criterion.CONTINUOUS_STUDY)),
        "student_review": _out_of_10(evaluation.score(Criterion.STUDENT_REVIEW_DIFFICULTY)),
        "summary": evaluation.summary,
        "reasoning": _reasoning(evaluation),
        "ranking": evaluation.ranking.value,
        "point": _out_of_10(evaluation.point),
        "confidence": round(evaluation.confidence * 10, 1),
        "weekly_hours_min": evaluation.weekly_hours.min,
        "weekly_hours_max": evaluation.weekly_hours.max,
    }


def _assessments(syllabus: SyllabusResult) -> list[dict]:
    """One row per graded item: "4 labs x 5%" becomes four rows of 0.05, each with its own date if known.
    score_percent can add up to more than 1 when the course offers extra credit."""
    rows = []
    for assessment in syllabus.assessments:
        for index in range(assessment.count):
            due = assessment.due_dates[index] if index < len(assessment.due_dates) else None
            rows.append({
                "id": len(rows) + 1,
                "type": assessment.kind.value,
                "score_percent": round(assessment.weight_each / 100, 4),
                "date": due.isoformat() if due else None,
            })
    return rows


def _evidence(evaluation: CourseEvaluation) -> list[dict]:
    """Evidence behind all criteria, each fact once."""
    rows, seen = [], set()
    for score in evaluation.criteria:
        for item in score.evidence:
            link = str(item.link) if item.link else None
            if (link, item.text) in seen:
                continue
            seen.add((link, item.text))
            rows.append({"id": len(rows) + 1, "link": link, "content_summary": item.text})
    return rows


def _reasoning(evaluation: CourseEvaluation) -> str:
    lines = [
        f"{CRITERION_LABELS[score.criterion]} ({_out_of_10(score.score):g}/10): {score.reasoning}"
        for score in evaluation.criteria
    ]
    lines.append(f"Weekly study time: {evaluation.weekly_hours.min}-{evaluation.weekly_hours.max} hours outside class.")
    if evaluation.warnings:
        lines += ["", "Notes:", *(f"- {warning}" for warning in evaluation.warnings)]
    return "\n".join(lines)


def _out_of_10(score: float) -> float:
    return round(score / 10, 1)


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


def delete_course(db: Session, user_id: int, course_id: int) -> bool:
    """Delete one of the user's courses. Returns False when it doesn't exist."""
    course = get_course(db, user_id, course_id)
    if not course:
        return False
    db.delete(course)
    db.commit()
    return True


def course_to_response(course: Course) -> CourseResponse:
    return CourseResponse(
        id=course.id,
        course_semester=course.course_semester,
        # normalized on read too, so rows saved before normalization look the same
        course_name=normalize_course_title(course.course_name) if course.course_name else None,
        professor_name=course.professor_name,
        course_code=normalize_course_code(course.course_code) if course.course_code else None,
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
        weekly_hours_min=course.weekly_hours_min,
        weekly_hours_max=course.weekly_hours_max,
    )

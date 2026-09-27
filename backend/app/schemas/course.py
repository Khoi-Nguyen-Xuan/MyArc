from datetime import date as date_type

from pydantic import BaseModel, ConfigDict, Field


class AssessmentItem(BaseModel):
    type: str
    score_percent: float  # 0.05 = 5% of the grade; the sum can pass 1 when there is extra credit
    date: date_type | None = None  # None when the syllabus gives no date


class EvidenceItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    link: str | None = None  # None for facts from the syllabus itself
    content_summary: str = Field(alias="content-summary")


class CourseResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # not in the original spec, but needed so GET / results can be used to
    # call GET /:id — flagged separately.
    id: int

    course_semester: str | None = None
    course_name: str | None = None
    professor_name: str | None = None
    course_code: str | None = None

    evaluate: list[AssessmentItem] = Field(default_factory=list)

    short_review: str | None = Field(default=None, alias="short-review")

    workload: float | None = None
    conceptual_difficulty: float | None = Field(default=None, alias="conceptual difficult")
    assessment_weighting: float | None = None
    continious_study_requirement: float | None = Field(
        default=None, alias="continious-study requirement"
    )
    student_review: float | None = Field(default=None, alias="student-review difficulity")

    evidence: list[EvidenceItem] = Field(default_factory=list)

    summary: str | None = None
    reasoning: str | None = None
    ranking: str | None = None
    point: float | None = None
    confidence: float | None = None

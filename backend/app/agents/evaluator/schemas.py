"""Contracts for the Evaluator agent: what it returns for one course.

The evaluator combines the syllabus agent's `SyllabusResult` (what the course
IS) with the research agent's `ResearchResult` (what students SAY) into the
scores the dashboard shows:

- six criteria, each scored 0-100 (100 = most demanding), with the reasoning
  and evidence behind it for the "Why?" drawer;
- the weighted `point` and its S-D `ranking`, both COMPUTED here from the six
  scores with the project's formula, never written by the LLM;
- confidence, weekly hours, a one-line review and a short summary.

Three criteria can be counted from the syllabus and student claims, so code
scores them; the other three need judgment, so the LLM scores them. Each score
records which one it came from (`scored_by`).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, HttpUrl, computed_field, model_validator


class Criterion(StrEnum):
    WORKLOAD = "workload"  # hours of work overall
    CONCEPTUAL_DIFFICULTY = "conceptual_difficulty"  # how hard the ideas are
    DEADLINE_PRESSURE = "deadline_pressure"  # how many graded items, how often
    ASSESSMENT_WEIGHTING = "assessment_weighting"  # how much of the grade rides on exams
    CONTINUOUS_STUDY = "continuous_study"  # must you keep up weekly, or can you cram?
    STUDENT_REVIEW_DIFFICULTY = "student_review_difficulty"  # how hard students say it is


class ScoredBy(StrEnum):
    CODE = "code"  # counted from the data: exact and repeatable
    LLM = "llm"  # judged by the LLM from the evidence


class Rank(StrEnum):
    S = "S"  # most demanding
    A = "A"
    B = "B"
    C = "C"
    D = "D"  # least demanding


# The project's formula. The weights add up to 1, so `point` stays on the 0-100 scale.
CRITERION_WEIGHTS: dict[Criterion, float] = {
    Criterion.WORKLOAD: 0.25,
    Criterion.CONCEPTUAL_DIFFICULTY: 0.20,
    Criterion.DEADLINE_PRESSURE: 0.20,
    Criterion.ASSESSMENT_WEIGHTING: 0.15,
    Criterion.CONTINUOUS_STUDY: 0.10,
    Criterion.STUDENT_REVIEW_DIFFICULTY: 0.10,
}

# Fixed cut-offs on `point`, highest first: a point of at least 80 is S, and so on.
RANK_CUTOFFS: list[tuple[Rank, float]] = [
    (Rank.S, 80),
    (Rank.A, 65),
    (Rank.B, 50),
    (Rank.C, 35),
    (Rank.D, 0),
]


class EvidenceItem(BaseModel):
    """One fact behind a score: a line of the syllabus or a student's claim."""

    text: str = Field(description='The fact in plain words, e.g. "Labs take 10-12 hours a week near the end of term."')
    link: HttpUrl | None = Field(default=None, description="Reddit thread of a student claim; None for syllabus facts.")
    quote: str | None = Field(default=None, description="The exact words from the syllabus or the thread.")
    page: int | None = Field(default=None, ge=1, description="Syllabus page, when the syllabus is a PDF.")


class CriterionScore(BaseModel):
    criterion: Criterion
    score: float = Field(ge=0, le=100, description="0 = not demanding at all, 100 = extremely demanding.")
    scored_by: ScoredBy
    reasoning: str = Field(description="One or two sentences on why this score.")
    evidence: list[EvidenceItem] = Field(default_factory=list)


class WeeklyHours(BaseModel):
    """Recommended study time outside class, as a range."""

    min: int = Field(ge=0, le=60)
    max: int = Field(ge=0, le=60)

    @model_validator(mode="after")
    def min_not_above_max(self) -> Self:
        if self.min > self.max:
            raise ValueError(f"min ({self.min}) is above max ({self.max})")
        return self


class CourseEvaluation(BaseModel):
    """Everything the dashboard shows for one course."""

    course_code: str
    criteria: list[CriterionScore] = Field(description="Exactly one score per criterion.")
    weekly_hours: WeeklyHours
    confidence: float = Field(ge=0, le=1, description="How much to trust these scores: 0.87 is shown as 87%.")
    short_review: str = Field(description='One line for the course card, e.g. "Heavy weekly labs; exams are harsh."')
    summary: str = Field(description="A short paragraph explaining the ranking.")
    warnings: list[str] = Field(default_factory=list, description='e.g. "Only 2 student threads found."')

    @model_validator(mode="after")
    def one_score_per_criterion(self) -> Self:
        scored = [item.criterion.value for item in self.criteria]
        missing = sorted({criterion.value for criterion in Criterion} - set(scored))
        repeated = sorted({criterion for criterion in scored if scored.count(criterion) > 1})
        if missing or repeated:
            raise ValueError(f"each criterion must appear once; missing {missing}, repeated {repeated}")
        return self

    def score(self, criterion: Criterion) -> float:
        return next(item.score for item in self.criteria if item.criterion is criterion)

    @computed_field
    @property
    def point(self) -> float:
        """The weighted formula, 0-100."""
        return round(sum(weight * self.score(criterion) for criterion, weight in CRITERION_WEIGHTS.items()), 1)

    @computed_field
    @property
    def ranking(self) -> Rank:
        return next(rank for rank, cutoff in RANK_CUTOFFS if self.point >= cutoff)

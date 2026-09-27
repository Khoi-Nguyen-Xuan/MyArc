"""Contracts for the Syllabus agent: what goes in and what comes out.

The syllabus agent reads one uploaded syllabus (PDF or Word) and returns how demanding a course is: 
what is graded, how much each worth, and when it is due. 

Downstream:
- the calendar and weekly-workload view use each assessment's due dates;
- the Evaluator uses the weights and policies to score exam pressure,
  deadline density and so on;
- the "Why?" drawer shows `source.quote` so a student can see where a fact
  came from.

Weights above 100% are normal: some courses offer extra marks on purpose
(CMPUT 201 adds up to 104%). Only totals below 100% get a warning.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.course_codes import normalize_course_code


class AssessmentKind(StrEnum):
    """What kind of graded work an assessment is."""

    ASSIGNMENT = "assignment"
    LAB = "lab"
    QUIZ = "quiz"
    MIDTERM = "midterm"
    FINAL_EXAM = "final_exam"
    PROJECT = "project"
    PAPER = "paper"  # essays, term papers, reports
    PRESENTATION = "presentation"
    PARTICIPATION = "participation"  # attendance, clickers, discussion posts
    OTHER = "other"


class PolicyTopic(StrEnum):
    """Course rules that change how stressful a course is."""

    LATE_WORK = "late_work"  # "No late submissions are accepted."
    MISSED_EXAM = "missed_exam"  # "No deferred midterm; its weight moves to the final."
    AI_USE = "ai_use"
    COLLABORATION = "collaboration"
    OTHER = "other"


class SyllabusRequest(BaseModel):
    """What the agent knows before reading the file"""

    model_config = ConfigDict(str_strip_whitespace=True)

    course_code: str | None = Field(
        default=None,
        description='The code the student added the syllabus under, e.g. "BIOIN 301". '
        "None: the agent reads it from the syllabus.",
    )
    term: str | None = Field(default=None, description='The study term, e.g. "Fall 2026".')

    @field_validator("course_code")
    @classmethod
    def normalize_code(cls, value: str | None) -> str | None:
        return normalize_course_code(value) if value else None


class SourceRef(BaseModel):
    """Where in the syllabus a fact comes from"""

    quote: str = Field(description="Short text from the syllabus that states the fact.")
    page: int | None = Field(default=None, ge=1, description="PDF page number. None for Word documents.")


class Assessment(BaseModel):
    """One graded component"""

    name: str = Field(description='As the syllabus names it, e.g. "Quizzes" or "Midterm #1".')
    kind: AssessmentKind
    count: int = Field(default=1, ge=1, description="How many of them: 9 for nine quizzes.")
    weight_each: float = Field(gt=0, le=100, description="Percent of the final grade for ONE item")
    due_dates: list[date] = Field(
        default_factory=list,
        description="Dates the syllabus gives. Often fewer than `count`, or none at all.",
    )
    notes: str | None = Field(
        default=None,
        description='Anything that changes the numbers or dates: "lowest quiz dropped", "final exam date TBD".',
    )
    source: SourceRef

    @property
    def total_weight(self) -> float:
        """Percent of the final grade for all items together"""
        return self.count * self.weight_each

    @model_validator(mode="after")
    def dates_fit_count(self) -> Self:
        if len(self.due_dates) > self.count:
            raise ValueError(f"{len(self.due_dates)} due dates for only {self.count} item(s)")
        self.due_dates.sort()
        return self


class Policy(BaseModel):
    """A course rule, summarized in one or two plain sentences."""

    topic: PolicyTopic
    summary: str
    source: SourceRef


class SyllabusResult(BaseModel):
    """Everything the agent extracted from one syllabus."""

    request: SyllabusRequest
    course_title: str | None = None
    term: str | None = Field(default=None, description="The term the syllabus itself names.")
    instructors: list[str] = Field(default_factory=list, description="Names only; the researcher searches for them.")
    assessments: list[Assessment] = Field(default_factory=list)
    policies: list[Policy] = Field(default_factory=list)
    warnings: list[str] = Field(
        default_factory=list,
        description='Problems found, e.g. "Weights add up to 95%; an assessment may be missing." Shown to the student.',
    )

    @property
    def total_weight(self) -> float:
        return sum(assessment.total_weight for assessment in self.assessments)

    @property
    def extra_credit(self) -> float:
        """Percent available beyond 100, e.g. 4 when the weights add up to 104%. Intended by the course."""
        return max(self.total_weight - 100, 0.0)

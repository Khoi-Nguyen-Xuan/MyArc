"""Contracts for the Researcher agent: define what goes in and what comes out.

Job: The researcher main task is to find what students say about a course on the internet (mainly Reddit) and returns
*atomic, cited claims* instead of a prose summary. Two agents rely on this shape:

- the Evaluator, which scores the course from the claims, and
- the Critic, which checks that the claims are recent, about the right
  professor, and numerous enough to trust.
"""

from __future__ import annotations

import re
from datetime import date
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

#We going to trim if the comment/review is longer than this 
MAX_QUOTE_LENGTH = 300

#Extract course code with regex 
_COURSE_CODE = re.compile(r"^([A-Z]+)\s*(\d{3}[A-Z]?)$")


class SourceType(StrEnum):
    """Where a piece of evidence came from."""

    REDDIT = "reddit"
    PROFESSOR_REVIEW = "professor_review"  # e.g. from RateMyProfessors
    UNIVERSITY_PAGE = "university_page"  # official course/ department pages
    FORUM = "forum"  # other discussion boards
    OTHER = "other"


class Aspect(StrEnum):
    """Topic of a claim. This will also be the Evaluator's scoring dimensions."""

    WORKLOAD = "workload"
    CONCEPTUAL_DIFFICULTY = "conceptual_difficulty"
    EXAM_PRESSURE = "exam_pressure"
    ASSIGNMENTS_PROJECTS = "assignments_projects"
    CONTINUOUS_STUDY = "continuous_study"  # like are you required to keep up weekly, or can you cram in a few day?
    GRADING = "grading"
    TEACHING = "teaching"
    OTHER = "other"


class Signal(StrEnum):
    """Does the claim make the course look more or less demanding than other courses?"""

    HARDER = "harder"
    EASIER = "easier"
    NEUTRAL = "neutral"


class ProfessorMatch(StrEnum):
    """Whether a claim is about the professor teaching the student's section."""

    SAME = "same"
    DIFFERENT = "different"
    UNKNOWN = "unknown"  # the source doesn't say who taught it


class ResearchRequest(BaseModel):
    """Everything the researcher needs to know about one course."""

    model_config = ConfigDict(str_strip_whitespace=True)

    course_code: str = Field(description='Normalized all to "DEPT 123", e.g. "CMPUT 301".')
    university: str = "University of Alberta"
    course_title: str | None = None
    professor: str | None = None
    term: str | None = Field(default=None, description='e.g. "Fall 2026".')
    follow_up_queries: list[str] = Field(
        default_factory=list,
        description="Extra searches the Critic asks for on a revision pass.",
    )

    @field_validator("course_code")
    @classmethod
    def normalize_course_code(cls, value: str) -> str:
        """Turn "cmput301" or "CMPUT  301" into "CMPUT 301" so searches and cache keys agree."""
        compact = " ".join(value.upper().split())
        match = _COURSE_CODE.match(compact)
        return f"{match[1]} {match[2]}" if match else compact


class Source(BaseModel):
    """A web page the researcher read."""

    url: HttpUrl
    title: str
    source_type: SourceType
    published_at: date | None = Field(
        default=None,
        description="None when the page shows no date; the Critic treats undated sources as possibly stale.",
    )


class EvidenceClaim(BaseModel):
    """One atomic statement a source makes about the course."""

    claim: str = Field(description="One statement in plain words, e.g. 'The group project takes most of the term.'")
    quote: str | None = Field(default=None, description="Short evidence that supports the claim.")
    source_url: HttpUrl
    aspect: Aspect
    signal: Signal
    professor_match: ProfessorMatch
    relevance: float = Field(
        ge=0.0,
        le=1.0,
        description="How directly the claim is about this course.",
    )

    @field_validator("quote")
    @classmethod
    def trim_quote(cls, value: str | None) -> str | None:
        """Trim long quotes instead of rejecting them"""
        if value is None or len(value) <= MAX_QUOTE_LENGTH:
            return value
        return value[: MAX_QUOTE_LENGTH - 1].rstrip() + "…"


class ResearchResult(BaseModel):
    """Output of one research run for one course."""

    request: ResearchRequest
    sources: list[Source] = Field(default_factory=list)
    claims: list[EvidenceClaim] = Field(default_factory=list)
    queries_run: list[str] = Field(
        default_factory=list,
        description="Kept so a revision pass doesn't repeat the same searches.",
    )

    @model_validator(mode="after")
    def claims_cite_known_sources(self) -> Self:
        """Every claim must point at a page listed in `sources`, or the "Why?" popup can't link it."""
        known_urls = {str(source.url) for source in self.sources}
        orphans = [str(claim.source_url) for claim in self.claims if str(claim.source_url) not in known_urls]
        if orphans:
            raise ValueError(f"Claims cite sources missing from `sources`: {orphans}")
        return self

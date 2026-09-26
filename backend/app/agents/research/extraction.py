"""
Turns one web page into cited evidence claims, using the LLM API.

The split of work is:
- the LLM decides what a page SAYS (the claims, their aspect and signal);
- the code decides what a page IS (its URL, its source type) and what to keep.
=> every claim is guaranteed to point at a real page
"""

from __future__ import annotations

from datetime import date
from functools import cache
from pathlib import Path
from urllib.parse import urlsplit

from langchain.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.agents.research.queries import UNIVERSITY_DOMAINS
from app.agents.research.schemas import (
    Aspect,
    EvidenceClaim,
    ProfessorMatch,
    ResearchRequest,
    Signal,
    Source,
    SourceType,
)
from app.external.search_client import ExtractedPage

PROMPT_PATH = Path(__file__).parents[1] / "prompts" / "research_agent.md"

MIN_RELEVANCE = 0.5  # drops claims the LLM itself was unsure belong to this course (0.4 in the prompt's scale)


# What the LLM returns.
# structured output needs every field to be required
class ExtractedClaim(BaseModel):
    claim: str
    quote: str | None
    aspect: Aspect
    signal: Signal
    professor_match: ProfessorMatch
    relevance: float = Field(description="0 to 1")


class PageExtraction(BaseModel):
    is_about_course: bool
    published_at: str | None = Field(description="YYYY-MM-DD, or null if the page shows no date")
    claims: list[ExtractedClaim]


async def extract_evidence(
    llm: BaseChatModel,
    request: ResearchRequest,
    page: ExtractedPage,
    title: str,
) -> tuple[Source | None, list[EvidenceClaim]]:
    """Ask the LLM for the claims on one page and turn them into evidence.
    Returns (None, []) when the page turns out to be about something else.
    """
    extractor = llm.with_structured_output(PageExtraction)
    extraction: PageExtraction = await extractor.ainvoke(build_messages(request, page))
    return to_evidence(extraction, request, page, title)


def build_messages(request: ResearchRequest, page: ExtractedPage) -> list[SystemMessage | HumanMessage]:
    course_lines = [
        f"Course: {request.course_code}" + (f" ({request.course_title})" if request.course_title else ""),
        f"University: {request.university}",
        f"Professor: {request.professor or 'not given'}",
        f"Page URL: {page.url}",
    ]
    user_message = "\n".join(course_lines) + f"\n\n<page>\n{page.content}\n</page>"
    return [SystemMessage(_system_prompt()), HumanMessage(user_message)]


def to_evidence(
    extraction: PageExtraction,
    request: ResearchRequest,
    page: ExtractedPage,
    title: str,
) -> tuple[Source | None, list[EvidenceClaim]]:
    """Validate the LLM's output and attach the page's URL to every claim."""
    if not extraction.is_about_course:
        return None, []

    claims = [
        EvidenceClaim(
            claim=item.claim,
            quote=item.quote,
            source_url=page.url,
            aspect=item.aspect,
            signal=item.signal,
            professor_match=item.professor_match if request.professor else ProfessorMatch.UNKNOWN,
            relevance=min(max(item.relevance, 0.0), 1.0),
        )
        for item in extraction.claims
        if item.relevance >= MIN_RELEVANCE and item.claim.strip()
    ]
    if not claims:
        return None, []

    source = Source(
        url=page.url,
        title=title,
        source_type=source_type_for(page.url, request.university),
        published_at=page.published_at or _parse_date(extraction.published_at),  # a real date beats the LLM's reading
    )
    return source, claims


def source_type_for(url: str, university: str) -> SourceType:
    """Classify a page by its domain"""
    host = urlsplit(url).netloc.lower()
    university_domain = UNIVERSITY_DOMAINS.get(university)

    if host == "reddit.com" or host.endswith(".reddit.com"):
        return SourceType.REDDIT
    if host.endswith("ratemyprofessors.com"):
        return SourceType.PROFESSOR_REVIEW
    if university_domain and (host == university_domain or host.endswith("." + university_domain)):
        return SourceType.UNIVERSITY_PAGE
    return SourceType.OTHER


def _parse_date(value: str | None) -> date | None:
    """Accept only a real YYYY-MM-DD date that isn't in the future. Anything else counts as undated."""
    if not value:
        return None
    try:
        parsed = date.fromisoformat(value.strip())
    except ValueError:
        return None
    return parsed if parsed <= date.today() else None


@cache
def _system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")

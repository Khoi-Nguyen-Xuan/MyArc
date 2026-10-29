"""Decides which web searches for the researcher.

The searches are templates, not LLM-written => predictable

The rounds:
- Round 1: searches in the university's subreddit (Reddit API or Tavily).
- Round 2: only runs when round 1 found TOO FEW Reddit threads (the graph decides
  that). More Reddit searches with other ways students name the course, plus one
  web search for student review sites. Official pages and course-document sites
  are EXCLUDED.
"""

from __future__ import annotations

from collections.abc import Iterable

from app.agents.research.schemas import ResearchRequest
from app.agents.research.state import PlannedQuery

SUBREDDITS: dict[str, str] = {
    "University of Alberta": "uAlberta",
}

UNIVERSITY_DOMAINS: dict[str, str] = {
    "University of Alberta": "ualberta.ca",
}

# Sites that repost course documents (syllabi, notes, old exams), not student opinions.
DOCUMENT_SITES = ("coursehero.com", "cliffsnotes.com", "studocu.com", "quizlet.com", "chegg.com", "scribd.com")


def plan_queries(
    request: ResearchRequest,
    round_number: int,
    already_run: Iterable[PlannedQuery],
) -> list[PlannedQuery]:
    """Return the searches for this round, skipping any that already ran."""
    if request.follow_up_queries:
        candidates = [PlannedQuery(text, "reddit") for text in request.follow_up_queries]
    elif round_number == 1:
        candidates = _targeted_queries(request)
    else:
        candidates = _broader_queries(request)

    return _drop_repeats(candidates, already_run)


def _targeted_queries(request: ResearchRequest) -> list[PlannedQuery]:
    code = request.course_code
    queries = [
        _reddit(request, f'"{code}"'),  # every thread that names the course
        _reddit(request, f"{code} workload difficulty"),
    ]
    if request.professor:
        queries.append(_reddit(request, f"{code} {request.professor}"))
    return queries


def _broader_queries(request: ResearchRequest) -> list[PlannedQuery]:
    code = request.course_code
    queries = [
        _reddit(request, code.replace(" ", "")),
        _reddit(request, f"{code} exam"),
    ]
    if request.course_title:
        queries.append(_reddit(request, f'"{request.course_title}"'))  # e.g. "Calculus III"
    if request.professor:
        queries.append(_reddit(request, request.professor))
    queries.append(PlannedQuery(f'"{code}" {request.university} course review'))  # student review sites
    return queries


def _reddit(request: ResearchRequest, text: str) -> PlannedQuery:
    """A Reddit search"""
    scope = "" if subreddit_for(request.university) else f"{request.university} "
    return PlannedQuery(f"{scope}{text}", "reddit")


def excluded_web_domains(university: str) -> list[str]:
    """Web searches skip the university's own site and course-document sites."""
    own_site = UNIVERSITY_DOMAINS.get(university)
    return [*DOCUMENT_SITES, *([own_site] if own_site else [])]


def subreddit_for(university: str) -> str | None:
    """Return "uAlberta" for the University of Alberta."""
    return SUBREDDITS.get(university)


def _drop_repeats(candidates: list[PlannedQuery], already_run: Iterable[PlannedQuery]) -> list[PlannedQuery]:
    seen = set(already_run)
    planned: list[PlannedQuery] = []
    for query in candidates:
        if query not in seen:
            planned.append(query)
            seen.add(query)
    return planned

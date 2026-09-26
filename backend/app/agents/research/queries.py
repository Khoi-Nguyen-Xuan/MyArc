"""Decides which web searches for the researcher.

The searches are templates, not LLM-written => free, predictablE

The rounds work like this:

- Round 1: targeted searches in the university's subreddit.
- Round 2: only runs when round 1 found too little (the graph decides that).
  It widens the net to the whole web.
- Revision pass: when the Critic asks for specific follow-up searches, only
  those run.
"""

from __future__ import annotations

from collections.abc import Iterable

from app.agents.research.schemas import ResearchRequest
from app.agents.research.state import PlannedQuery

# SUPPORT UNIVERSITY OF ALBERTA FOR NOW
SUBREDDITS: dict[str, str] = {
    "University of Alberta": "uAlberta",
}

REDDIT = ("reddit.com",)


def plan_queries(
    request: ResearchRequest,
    round_number: int,
    already_run: Iterable[PlannedQuery],
) -> list[PlannedQuery]:
    """Return the searches for this round, skipping any that already ran."""
    if request.follow_up_queries:
        candidates = [PlannedQuery(text) for text in request.follow_up_queries]
    elif round_number == 1:
        candidates = _targeted_queries(request)
    else:
        candidates = _broader_queries(request)

    return _drop_repeats(candidates, already_run)


def _targeted_queries(request: ResearchRequest) -> list[PlannedQuery]:
    code = request.course_code
    community = _reddit_community(request)

    queries = [
        PlannedQuery(f"{community} {code} workload difficulty", REDDIT),
        PlannedQuery(f"{community} {code} exams assignments advice", REDDIT),
    ]
    if request.professor:
        queries.append(PlannedQuery(f"{community} {code} {request.professor}", REDDIT))
    return queries


def _broader_queries(request: ResearchRequest) -> list[PlannedQuery]:
    code = request.course_code
    subject = f"{code} {request.course_title}" if request.course_title else code

    queries = [
        PlannedQuery(f'"{code}" {request.university} course review'),
        PlannedQuery(f"{subject} {request.university} how hard is it"),
    ]
    if request.professor:
        queries.append(PlannedQuery(f"{request.professor} {request.university} professor reviews"))
    return queries


def _reddit_community(request: ResearchRequest) -> str:
    """Return "r/uAlberta" when we know the subreddit, otherwise the university's name."""
    subreddit = SUBREDDITS.get(request.university)
    return f"r/{subreddit}" if subreddit else request.university


def _drop_repeats(candidates: list[PlannedQuery], already_run: Iterable[PlannedQuery]) -> list[PlannedQuery]:
    seen = set(already_run)
    planned: list[PlannedQuery] = []
    for query in candidates:
        if query not in seen:
            planned.append(query)
            seen.add(query)
    return planned

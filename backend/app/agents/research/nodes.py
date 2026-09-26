"""
Nodes of the research graph.
"""

from __future__ import annotations

import asyncio
import logging

from langgraph.runtime import Runtime

from app.agents.research.extraction import extract_evidence
from app.agents.research.pages import choose_pages, strip_markup, truncate
from app.agents.research.queries import plan_queries
from app.agents.research.schemas import ResearchResult
from app.agents.research.state import PageTask, ResearchContext, ResearchState
from app.external.search_client import SearchClientError, SearchHit

logger = logging.getLogger(__name__)

# HTTP statuses that mean the LLM is misconfigured, not that one page was bad:
# 401 bad or expired key, 403 no access, 404 unknown model name.
_SETUP_ERROR_STATUSES = {401, 403, 404}


async def plan_searches(state: ResearchState, runtime: Runtime[ResearchContext]) -> dict:
    """Start a new round, decide which searches it runs."""
    round_number = state["round_number"] + 1
    planned = plan_queries(state["request"], round_number, state["queries_run"])
    return {"round_number": round_number, "planned_queries": planned}


async def search_web(state: ResearchState, runtime: Runtime[ResearchContext]) -> dict:
    """Run this round's searches in parallel and choose which result pages to read.

    One failed search is logged and skipped.
    """
    search = runtime.context.search
    budget = runtime.context.budget
    queries = state["planned_queries"]

    outcomes = await asyncio.gather(
        *(
            search.search(query.text, max_results=budget.results_per_query, include_domains=query.domains)
            for query in queries
        ),
        return_exceptions=True,
    )

    hits: list[SearchHit] = []
    failures = 0
    for query, outcome in zip(queries, outcomes, strict=True):
        if isinstance(outcome, SearchClientError):
            failures += 1
            logger.warning("Search failed, skipping it: %s (%s)", query, outcome)
        elif isinstance(outcome, BaseException):
            raise outcome  # a bug in code
        else:
            hits.extend(outcome)

    if queries and failures == len(queries):
        raise SearchClientError(f"All {failures} searches failed in round {state['round_number']}.")

    to_read = choose_pages(hits, already_seen=state["urls_seen"], limit=budget.max_pages_per_round)
    return {
        "queries_run": queries,
        "to_read": to_read,
        "urls_seen": [hit.url for hit in to_read],
    }


async def read_pages(state: ResearchState, runtime: Runtime[ResearchContext]) -> dict:
    """Fetch the full text of the chosen pages, strip menus and links, and cut to the budget's length."""
    to_read = state["to_read"]
    if not to_read:
        return {"pages": []}

    try:
        # "advanced": Reddit blocks the basic fetcher, and most of our pages are Reddit threads.
        batch = await runtime.context.search.extract([hit.url for hit in to_read], depth="advanced")
    except SearchClientError as exc:
        logger.warning("Page extraction failed for round %s: %s", state["round_number"], exc)
        return {"pages": []}

    if batch.failed_urls:
        logger.info("Could not read %d pages: %s", len(batch.failed_urls), batch.failed_urls)

    max_chars = runtime.context.budget.max_chars_per_page
    return {"pages": [truncate(strip_markup(page), max_chars) for page in batch.pages]}


async def extract_claims(task: PageTask, runtime: Runtime[ResearchContext]) -> dict:
    """Pull claims out of ONE page. The graph runs one copy of this node per page, in parallel.

    A page that fails (LLM error, rate limit, malformed output) is logged and skipped:
    """
    page = task["page"]
    try:
        source, claims = await extract_evidence(runtime.context.llm, task["request"], page, task["title"])
    except Exception as exc:
        if _is_setup_error(exc):
            raise  # bad key or unknown model: every page would fail the same way, so stop the run
        logger.warning("Claim extraction failed, skipping page %s: %s: %s", page.url, type(exc).__name__, exc)
        return {"sources": [], "claims": []}

    if source is None:
        logger.info("Page not about the course, skipping: %s", page.url)
        return {"sources": [], "claims": []}
    return {"sources": [source], "claims": claims}


async def review_round(state: ResearchState, runtime: Runtime[ResearchContext]) -> dict:
    """Join point after the parallel branches: report progress and decide whether to search again."""
    keep_searching = should_search_again(state, runtime.context)
    logger.info(
        "Research round %d for %s: %d claims from %d sources so far (%s)",
        state["round_number"],
        state["request"].course_code,
        len(state["claims"]),
        len(state["sources"]),
        "searching again" if keep_searching else "done",
    )
    return {"keep_searching": keep_searching}


def should_search_again(state: ResearchState, context: ResearchContext) -> bool:
    """Stop when we have enough claims, ran out of rounds, or finished a Critic revision pass."""
    if len(state["claims"]) >= context.budget.enough_claims:
        return False
    if state["round_number"] >= context.budget.max_rounds:
        return False
    return not state["request"].follow_up_queries


async def assemble_result(state: ResearchState, runtime: Runtime[ResearchContext]) -> dict:
    """Package everything the run found into the `ResearchResult` contract."""
    result = ResearchResult(
        request=state["request"],
        sources=state["sources"],
        claims=state["claims"],
        queries_run=[str(query) for query in state["queries_run"]],
    )
    return {"result": result}


def _is_setup_error(exc: Exception) -> bool:
    """True for errors no retry or other page can fix. OpenAI's and Anthropic's errors both carry `status_code`."""
    return getattr(exc, "status_code", None) in _SETUP_ERROR_STATUSES

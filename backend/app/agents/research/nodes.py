"""
Nodes of the research graph.
"""

from __future__ import annotations

import asyncio
import logging

from langgraph.runtime import Runtime

from app.agents.research.pages import choose_pages, truncate
from app.agents.research.queries import plan_queries
from app.agents.research.state import ResearchContext, ResearchState
from app.external.search_client import SearchClientError, SearchHit

logger = logging.getLogger(__name__)


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
    """Fetch the full text of the chosen pages, cut to the budget's length."""
    to_read = state["to_read"]
    if not to_read:
        return {"pages": []}

    try:
        batch = await runtime.context.search.extract([hit.url for hit in to_read])
    except SearchClientError as exc:
        logger.warning("Page extraction failed for round %s: %s", state["round_number"], exc)
        return {"pages": []}

    if batch.failed_urls:
        logger.info("Could not read %d pages: %s", len(batch.failed_urls), batch.failed_urls)

    max_chars = runtime.context.budget.max_chars_per_page
    return {"pages": [truncate(page, max_chars) for page in batch.pages]}

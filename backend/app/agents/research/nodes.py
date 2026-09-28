"""
Nodes of the research graph.
"""

from __future__ import annotations

import asyncio
import logging

from langgraph.runtime import Runtime

from app.agents.research.extraction import extract_evidence
from app.agents.research.pages import choose_pages, is_on_domains, is_reddit_url, strip_markup, truncate
from app.agents.research.queries import excluded_web_domains, plan_queries, subreddit_for
from app.agents.research.schemas import ResearchResult, SourceType
from app.agents.research.sources import FETCH_ERRORS, read_with_tavily
from app.agents.research.state import PageTask, PlannedQuery, ResearchContext, ResearchState
from app.core.timing import log_duration
from app.external.llm_client import is_setup_error
from app.external.search_client import SearchClientError, SearchHit

logger = logging.getLogger(__name__)


async def plan_searches(state: ResearchState, runtime: Runtime[ResearchContext]) -> dict:
    """Start a new round, decide which searches it runs."""
    round_number = state["round_number"] + 1
    planned = plan_queries(state["request"], round_number, state["queries_run"])
    return {"round_number": round_number, "planned_queries": planned}


async def search_web(state: ResearchState, runtime: Runtime[ResearchContext]) -> dict:
    """Run this round's searches in parallel and choose which result pages to read.

    "reddit" searches go to the Reddit source (API or Tavily), "web" searches to Tavily.
    One failed search is logged and skipped.
    """
    context = runtime.context
    subreddit = subreddit_for(state["request"].university)
    excluded = excluded_web_domains(state["request"].university)
    queries = state["planned_queries"]

    def run(query: PlannedQuery):
        limit = context.budget.results_per_query
        if query.where == "reddit":
            return context.reddit.find_threads(subreddit, query.text, limit)
        return context.search.search(query.text, max_results=limit, exclude_domains=excluded)

    label = f"{state['request'].course_code} · research round {state['round_number']} · {len(queries)} searches"
    with log_duration(label):
        outcomes = await asyncio.gather(*(run(query) for query in queries), return_exceptions=True)

    hits: list[SearchHit] = []
    failures = 0
    for query, outcome in zip(queries, outcomes, strict=True):
        if isinstance(outcome, FETCH_ERRORS):
            failures += 1
            logger.warning("Search failed, skipping it: %s (%s)", query, outcome)
        elif isinstance(outcome, BaseException):
            raise outcome  # a bug in code
        else:
            hits.extend(outcome)

    if queries and failures == len(queries):
        raise SearchClientError(f"All {failures} searches failed in round {state['round_number']}.")

    hits = [hit for hit in hits if not is_on_domains(hit.url, excluded)]  # in case Tavily's filter lets one through
    to_read = choose_pages(hits, already_seen=state["urls_seen"], limit=context.budget.max_pages_per_round)
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

    reddit_urls = [hit.url for hit in to_read if is_reddit_url(hit.url)]
    web_urls = [hit.url for hit in to_read if not is_reddit_url(hit.url)]
    logger.info(
        "Reading %d Reddit threads via %s, and %d web pages...",
        len(reddit_urls),
        runtime.context.reddit.name,
        len(web_urls),
    )

    label = f"{state['request'].course_code} · research round {state['round_number']} · read {len(to_read)} pages"
    with log_duration(label):
        reddit_pages, web_pages = await asyncio.gather(
            runtime.context.reddit.read_threads(reddit_urls) if reddit_urls else _nothing(),
            read_with_tavily(runtime.context.search, web_urls) if web_urls else _nothing(),
        )
    pages = reddit_pages + web_pages
    if pages:
        logger.info("Read %d of %d pages. Extracting claims, 15-40s...", len(pages), len(to_read))

    max_chars = runtime.context.budget.max_chars_per_page
    return {"pages": [truncate(strip_markup(page), max_chars) for page in pages]}


async def _nothing() -> list:
    return []


async def extract_claims(task: PageTask, runtime: Runtime[ResearchContext]) -> dict:
    """Pull claims out of ONE page. The graph runs one copy of this node per page, in parallel.

    A page that fails (LLM error, rate limit, malformed output) is logged and skipped:
    """
    page = task["page"]
    try:
        # these run in parallel, so the round's extract time is the SLOWEST page, not the sum
        with log_duration(f"{task['request'].course_code} · extract claims ({len(page.content)} chars) {page.url}"):
            source, claims = await extract_evidence(runtime.context.llm, task["request"], page, task["title"])
    except Exception as exc:
        if is_setup_error(exc):
            raise  # bad key or unknown model: every page would fail the same way, so stop the run
        logger.warning("Claim extraction failed, skipping page %s: %s: %s", page.url, type(exc).__name__, exc)
        return {"sources": [], "claims": []}

    if source is None:
        logger.info("Page not about the course, skipping: %s", page.url)
        return {"sources": [], "claims": []}
    logger.info("%d claims from %s", len(claims), page.url)
    return {"sources": [source], "claims": claims}


async def review_round(state: ResearchState, runtime: Runtime[ResearchContext]) -> dict:
    """Join point after the parallel branches: report progress and decide whether to search again."""
    keep_searching = should_search_again(state, runtime.context)
    logger.info(
        "Research round %d for %s: %d claims from %d Reddit threads and %d other pages so far (%s)",
        state["round_number"],
        state["request"].course_code,
        len(state["claims"]),
        _reddit_threads(state),
        len(state["sources"]) - _reddit_threads(state),
        "searching again" if keep_searching else "done",
    )
    return {"keep_searching": keep_searching}


def should_search_again(state: ResearchState, context: ResearchContext) -> bool:
    """Stop when enough Reddit threads gave claims, we ran out of rounds, or finished a Critic revision pass.

    Counts threads, not claims: one long thread can yield 15 claims from two people,
    while five threads are five separate conversations.
    """
    if _reddit_threads(state) >= context.budget.enough_threads:
        return False
    if state["round_number"] >= context.budget.max_rounds:
        return False
    return not state["request"].follow_up_queries


def _reddit_threads(state: ResearchState) -> int:
    return sum(source.source_type is SourceType.REDDIT for source in state["sources"])


async def assemble_result(state: ResearchState, runtime: Runtime[ResearchContext]) -> dict:
    """Package everything the run found into the `ResearchResult` contract."""
    result = ResearchResult(
        request=state["request"],
        sources=state["sources"],
        claims=state["claims"],
        queries_run=[str(query) for query in state["queries_run"]],
    )
    return {"result": result}

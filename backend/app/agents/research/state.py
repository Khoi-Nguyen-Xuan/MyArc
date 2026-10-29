"""State for the research subgraph + run's budget.

LangGraph merges whatever each node returns into `ResearchState`:
"""

from __future__ import annotations

import operator
from dataclasses import dataclass
from typing import Annotated, Literal, TypedDict

from langchain.chat_models import BaseChatModel

from app.agents.research.schemas import EvidenceClaim, ResearchRequest, ResearchResult, Source
from app.agents.research.sources import RedditSource
from app.external.search_client import ExtractedPage, SearchClient, SearchHit


@dataclass(frozen=True, slots=True)
class PlannedQuery:
    """One search to run. Hashable => skip already-run searches"""

    text: str
    where: Literal["reddit", "web"] = "web"  # "reddit" runs through the RedditSource, "web" through Tavily

    def __str__(self) -> str:
        return f"[{self.where}] {self.text}"


@dataclass(frozen=True, slots=True)
class ResearchBudget:
    """Hard limits for one research run"""

    max_rounds: int = 2
    results_per_query: int = 5
    max_pages_per_round: int = 8
    max_chars_per_page: int = 12_000  # long Reddit threads get cut
    enough_threads: int = 5  # stop searching early once this many Reddit threads gave claims


@dataclass(frozen=True, slots=True)
class ResearchContext:
    """What every node needs: services and limits.
    Passed once through LangGraph's runtime context (`graph.ainvoke(..., context=...)`)
    """

    search: SearchClient
    llm: BaseChatModel
    reddit: RedditSource  # Reddit API, or Tavily
    budget: ResearchBudget = ResearchBudget()


class ResearchState(TypedDict):
    request: ResearchRequest
    round_number: int
    keep_searching: bool  # set by review_round after each round

    # Current round only (overwritten)
    planned_queries: list[PlannedQuery]
    to_read: list[SearchHit]  # search hits chosen to read in full
    pages: list[ExtractedPage]  # their extracted text, waiting for claim extraction

    # Whole run (accumulated)
    queries_run: Annotated[list[PlannedQuery], operator.add]
    urls_seen: Annotated[list[str], operator.add]  # never read the same page twice
    sources: Annotated[list[Source], operator.add]
    claims: Annotated[list[EvidenceClaim], operator.add]

    # Set once, by the last node
    result: ResearchResult


class PageTask(TypedDict):
    """Input of one parallel claim-extraction branch: one page, sent with `Send`."""

    request: ResearchRequest
    page: ExtractedPage
    title: str

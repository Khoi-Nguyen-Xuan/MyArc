"""State for the research subgraph, plus the run's budget.

LangGraph merges whatever each node returns into `ResearchState`:

- fields wrapped in `Annotated[list[...], operator.add]` ACCUMULATE: every
  round and every parallel branch appends to them;
- plain fields are OVERWRITTEN by the last node that wrote them. They hold
  work-in-progress for the current round only.
"""

from __future__ import annotations

import operator
from dataclasses import dataclass
from typing import Annotated, TypedDict

from langchain.chat_models import BaseChatModel

from app.agents.research.schemas import EvidenceClaim, ResearchRequest, ResearchResult, Source
from app.external.search_client import ExtractedPage, SearchClient, SearchHit


@dataclass(frozen=True, slots=True)
class PlannedQuery:
    """One web search to run. Hashable => skip already-run searches"""

    text: str
    domains: tuple[str, ...] = ()  # restrict results to these sites

    def __str__(self) -> str:
        return f"{self.text} [{', '.join(self.domains)}]" if self.domains else self.text


@dataclass(frozen=True, slots=True)
class ResearchBudget:
    """Hard limits for one research run"""

    max_rounds: int = 2
    results_per_query: int = 5
    max_pages_per_round: int = 8
    max_chars_per_page: int = 12_000  # long Reddit threads get cut
    pages_per_read: int = 2  # Reddit blocks more often when many threads are fetched at once
    enough_claims: int = 10  # stop searching early once agent have this many claims


@dataclass(frozen=True, slots=True)
class ResearchContext:
    """What every node needs but never changes during a run: services and limits.

    Passed once through LangGraph's runtime context (`graph.ainvoke(..., context=...)`)
    instead of being stored in the state, so tests can swap in a fake search client or LLM.
    """

    search: SearchClient
    llm: BaseChatModel
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

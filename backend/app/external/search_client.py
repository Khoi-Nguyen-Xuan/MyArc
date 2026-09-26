"""A thin wrapper around Tavily web search and page extraction.

Agents in our graph will never talk to Tavily directly. They call `SearchClient` function, which:

- returns small typed objects (`SearchHit`, `ExtractedPage`) instead of raw
  Tavily dicts, so a change in Tavily's response shape breaks this file only;
- turns every Tavily/ network failure into one `SearchClientError`, so
  callers have a single exception to handle.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Literal

import httpx
from tavily import AsyncTavilyClient
from tavily import errors as tavily_errors

MAX_URLS_PER_EXTRACT = 20

SearchDepth = Literal["basic", "advanced"]  # "advanced" costs 2 credits instead of 1

_TAVILY_FAILURES = (
    tavily_errors.BadRequestError,
    tavily_errors.ForbiddenError,
    tavily_errors.InvalidAPIKeyError,
    tavily_errors.MissingAPIKeyError,
    tavily_errors.TimeoutError,
    tavily_errors.UsageLimitExceededError,
    httpx.HTTPError,
)


class SearchClientError(Exception):
    """A search or extraction failed: bad key, quota exhausted, timeout or network error."""


@dataclass(frozen=True, slots=True)
class SearchHit:
    """One search result: enough to decide whether the page is worth reading in full."""
    url: str
    title: str
    snippet: str
    score: float  # Tavily's relevance score, 0 to 1


@dataclass(frozen=True, slots=True)
class ExtractedPage:
    """The readable text of one page, as markdown."""

    url: str
    content: str
    published_at: date | None = None  # known for Reddit API threads; Tavily pages don't have one


@dataclass(frozen=True, slots=True)
class ExtractionBatch:
    """List of extracting several pages at once."""
    pages: list[ExtractedPage]
    failed_urls: list[str]


class SearchClient:
    def __init__(self, api_key: str, *, timeout_seconds: float = 30.0) -> None:
        # Without a key the Tavily SDK silently falls back to a rate-limited "keyless" mode
        if not api_key:
            raise ValueError("TAVILY_API_KEY is not set.")
        self._tavily = AsyncTavilyClient(api_key=api_key)
        self._timeout_seconds = timeout_seconds

    async def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        depth: SearchDepth = "basic",
        include_domains: Sequence[str] | None = None,
        exclude_domains: Sequence[str] | None = None,
    ) -> list[SearchHit]:
        """Run one web search. `include_domains` restricts results to sites, `exclude_domains` drops sites."""
        try:
            response = await self._tavily.search(
                query,
                search_depth=depth,
                max_results=max_results,
                include_domains=list(include_domains) if include_domains else None,
                exclude_domains=list(exclude_domains) if exclude_domains else None,
                timeout=self._timeout_seconds,
            )
        except _TAVILY_FAILURES as exc:
            raise SearchClientError(f"Search failed for {query!r}: {exc}") from exc

        return [
            SearchHit(
                url=result["url"],
                title=result.get("title", ""),
                snippet=result.get("content", ""),
                score=float(result.get("score", 0.0)),
            )
            for result in response.get("results", [])
        ]

    async def extract(self, urls: Sequence[str], *, depth: SearchDepth = "basic") -> ExtractionBatch:
        """Fetch the full text of up to 20 pages in one call.

        "advanced" gets through sites that block the basic fetcher (Reddit does),
        at 2 credits per 5 pages instead of 1.
        """
        if not urls:
            return ExtractionBatch(pages=[], failed_urls=[])
        if len(urls) > MAX_URLS_PER_EXTRACT:
            raise ValueError(f"Tavily extracts at most {MAX_URLS_PER_EXTRACT} URLs per call, got {len(urls)}.")

        try:
            response = await self._tavily.extract(
                urls=list(urls),
                extract_depth=depth,
                format="markdown",
                timeout=self._timeout_seconds,
            )
        except _TAVILY_FAILURES as exc:
            raise SearchClientError(f"Extraction failed for {len(urls)} URLs: {exc}") from exc

        pages: list[ExtractedPage] = []
        failed_urls = [failure["url"] for failure in response.get("failed_results", [])]
        for result in response.get("results", []):
            content = (result.get("raw_content") or "").strip()
            if content:
                pages.append(ExtractedPage(url=result["url"], content=content))
            else:
                failed_urls.append(result["url"])  # an empty page is like a failed one

        return ExtractionBatch(pages=pages, failed_urls=failed_urls)

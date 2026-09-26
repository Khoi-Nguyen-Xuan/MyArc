"""Reddit's official API if have credentials, Tavily otherwise.

Both classes implement `RedditSource`, so the graph never knows which one it
is using.

|                       | RedditApiSource             | TavilyRedditSource (fallback)  |
|-----------------------|-----------------------------|--------------------------------|
| finds threads with    | Reddit's own search         | Tavily web search on reddit.com|
| reads threads with    | Reddit's JSON API           | Tavily extract (often blocked) |
| post dates            | exact                       | none                           |
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Protocol

from app.external.reddit_client import RedditClient, RedditClientError, RedditThread
from app.external.search_client import ExtractedPage, SearchClient, SearchClientError, SearchHit

logger = logging.getLogger(__name__)

# Errors that mean "this fetch failed", as opposed to a bug in our code.
FETCH_ERRORS = (SearchClientError, RedditClientError)

TAVILY_PAGES_PER_CALL = 2 

_THREAD_ID = re.compile(r"/comments/([a-z0-9]+)")


class RedditSource(Protocol):
    name: str

    async def find_threads(self, subreddit: str | None, query: str, limit: int) -> list[SearchHit]:
        """Search for threads. `subreddit` is None when we don't know the university's subreddit."""
        ...

    async def read_threads(self, urls: list[str]) -> list[ExtractedPage]:
        """Read threads in full. Threads that can't be read are logged and left out."""
        ...


class RedditApiSource:
    name = "Reddit API"

    def __init__(self, client: RedditClient, *, max_comments: int = 60, max_parallel: int = 4) -> None:
        self._client = client
        self._max_comments = max_comments
        self._max_parallel = max_parallel  # stays well under Reddit's ~100 requests per minute

    async def find_threads(self, subreddit: str | None, query: str, limit: int) -> list[SearchHit]:
        posts = await self._client.search(subreddit or "all", query, limit=limit)
        answered = [post for post in posts if post.num_comments > 0]  # unanswered questions carry no evidence
        # Reddit returns results by relevance. Turn the rank into a 0-1 score so `choose_pages` keeps that order.
        return [
            SearchHit(url=post.url, title=post.title, snippet="", score=1.0 - rank / (len(answered) + 1))
            for rank, post in enumerate(answered)
        ]

    async def read_threads(self, urls: list[str]) -> list[ExtractedPage]:
        semaphore = asyncio.Semaphore(self._max_parallel)

        async def read(url: str) -> ExtractedPage | None:
            post_id = thread_id_from_url(url)
            if post_id is None:
                logger.warning("Not a Reddit thread URL, skipping: %s", url)
                return None
            async with semaphore:
                try:
                    thread = await self._client.read_thread(post_id, max_comments=self._max_comments)
                except RedditClientError as exc:
                    logger.warning("Could not read Reddit thread %s: %s", url, exc)
                    return None
            return ExtractedPage(url=url, content=render_thread(thread), published_at=thread.post.created_at.date())

        pages = await asyncio.gather(*(read(url) for url in urls))
        return [page for page in pages if page is not None]


class TavilyRedditSource:
    name = "Tavily (fallback until the Reddit API is approved)"

    def __init__(self, search: SearchClient) -> None:
        self._search = search

    async def find_threads(self, subreddit: str | None, query: str, limit: int) -> list[SearchHit]:
        prefix = f"r/{subreddit} " if subreddit else ""
        return await self._search.search(f"{prefix}{query}", max_results=limit, include_domains=["reddit.com"])

    async def read_threads(self, urls: list[str]) -> list[ExtractedPage]:
        return await read_with_tavily(self._search, urls)


def build_reddit_source(
    search: SearchClient,
    *,
    user_agent: str | None,
    client_id: str | None,
    client_secret: str | None,
) -> RedditSource:
    """Use the Reddit API when all three settings are present, otherwise fall back to Tavily."""
    if user_agent and client_id and client_secret:
        return RedditApiSource(RedditClient(user_agent, client_id, client_secret))
    return TavilyRedditSource(search)


async def read_with_tavily(search: SearchClient, urls: list[str]) -> list[ExtractedPage]:
    """
    Read pages through Tavily a few at a time, then retry the failures once.
    """
    pages, failed = await _tavily_pass(search, urls)
    if failed:
        logger.info("Could not read %d pages, retrying once: %s", len(failed), failed)
        retried, failed = await _tavily_pass(search, failed)
        pages.extend(retried)
    if failed:
        logger.info("Gave up on %d pages: %s", len(failed), failed)
    return pages


async def _tavily_pass(search: SearchClient, urls: list[str]) -> tuple[list[ExtractedPage], list[str]]:
    """One pass over `urls` in sequential batches. Returns (pages read, URLs that failed)."""
    pages: list[ExtractedPage] = []
    failed: list[str] = []
    for start in range(0, len(urls), TAVILY_PAGES_PER_CALL):
        batch_urls = urls[start : start + TAVILY_PAGES_PER_CALL]
        try:
            # "advanced": Reddit blocks the basic fetcher entirely.
            batch = await search.extract(batch_urls, depth="advanced")
        except SearchClientError as exc:
            logger.warning("Page extraction failed for %s: %s", batch_urls, exc)
            failed.extend(batch_urls)
            continue
        pages.extend(batch.pages)
        failed.extend(batch.failed_urls)
    return pages, failed


def thread_id_from_url(url: str) -> str | None:
    """https://www.reddit.com/r/uAlberta/comments/1c7s1jc/is_math_214... -> "1c7s1jc"."""
    match = _THREAD_ID.search(url)
    return match[1] if match else None


def render_thread(thread: RedditThread) -> str:
    """Turn a thread into plain text for the LLM: the post, then comments indented by reply depth."""
    post = thread.post
    lines = [
        f"Title: {post.title}",
        f"Posted {post.created_at:%Y-%m-%d} · {post.score} upvotes · {post.num_comments} comments",
    ]
    if thread.body:
        lines += ["", thread.body]
    if thread.comments:
        lines += ["", "Comments, highest-voted first:"]
        for comment in thread.comments:
            indent = "  " * comment.depth
            body = comment.body.replace("\n", f"\n{indent}  ")
            lines.append(f"{indent}- [{comment.score} points] {body}")
    return "\n".join(lines)

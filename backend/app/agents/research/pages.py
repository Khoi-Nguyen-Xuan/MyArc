"""Helpers for picking which search results are worth reading"""

from __future__ import annotations

import dataclasses
from collections.abc import Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.external.search_client import ExtractedPage, SearchHit

# versions of a site that show the same page.
_HOST_PREFIXES = ("www.", "old.", "new.", "m.", "np.")


def normalize_url(url: str) -> str:
    """Give one page one URL => same thread found by two searches is read only once.

    https://old.reddit.com/r/uAlberta/comments/abc/title/?utm_source=x#top
    https://reddit.com/r/uAlberta/comments/abc/title
    """
    parts = urlsplit(url.strip())
    host = parts.netloc.lower()
    for prefix in _HOST_PREFIXES:
        if host.startswith(prefix):
            host = host.removeprefix(prefix)
            break

    tracking_free = [(key, value) for key, value in parse_qsl(parts.query) if not key.startswith("utm_")]
    query = "" if host == "reddit.com" else urlencode(tracking_free)  # Reddit query strings are never content
    return urlunsplit(("https", host, parts.path.rstrip("/"), query, ""))


def is_worth_reading(url: str) -> bool:
    """Skip Reddit pages that aren't discussion threads (subreddit front pages, user profiles)."""
    parts = urlsplit(url)
    if parts.netloc == "reddit.com":
        return "/comments/" in parts.path
    return True


def choose_pages(hits: Iterable[SearchHit], *, already_seen: Iterable[str], limit: int) -> list[SearchHit]:
    """Pick the best `limit` new pages: normalized, deduplicated, highest Tavily score first."""
    seen = set(already_seen)
    best_by_url: dict[str, SearchHit] = {}

    for hit in hits:
        url = normalize_url(hit.url)
        if url in seen or not is_worth_reading(url):
            continue
        current = best_by_url.get(url)
        if current is None or hit.score > current.score:
            best_by_url[url] = dataclasses.replace(hit, url=url)

    ranked = sorted(best_by_url.values(), key=lambda hit: hit.score, reverse=True)
    return ranked[:limit]


def truncate(page: ExtractedPage, max_chars: int) -> ExtractedPage:
    """Cut very long pages"""
    if len(page.content) <= max_chars:
        return page
    return dataclasses.replace(page, content=page.content[:max_chars])

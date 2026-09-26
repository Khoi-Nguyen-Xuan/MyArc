"""Searches and reads subreddit threads through Reddit's JSON API.

Two options:
- OAuth (production): with REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET, calls
  oauth.reddit.com with an app-only token. About 100 requests per minute.
- Public (development only): without credentials, calls www.reddit.com/....json.
  Heavily rate-limited (about 10 requests per minute) and not allowed for a
  production app under Reddit's terms.

Like search_client.py, this returns small typed objects and turns every
failure into one `RedditClientError`.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
OAUTH_BASE = "https://oauth.reddit.com"
PUBLIC_BASE = "https://www.reddit.com"

_REMOVED_BODIES = {"[deleted]", "[removed]"}


class RedditClientError(Exception):
    """A Reddit request failed"""


@dataclass(frozen=True, slots=True)
class RedditPost:
    """One thread as it appears in search results."""

    id: str  # Reddit's base-36 id, e.g. "1c7s1jc"
    title: str
    url: str  # https://www.reddit.com/r/<sub>/comments/<id>/<slug>
    created_at: datetime  # UTC
    score: int
    num_comments: int


@dataclass(frozen=True, slots=True)
class RedditComment:
    body: str
    score: int
    created_at: datetime  # UTC
    depth: int  # 0 = direct reply to the post, 1 = reply to that, ...


@dataclass(frozen=True, slots=True)
class RedditThread:
    """A post plus its comments, highest-voted first."""

    post: RedditPost
    body: str  # the post's own text; 
    comments: list[RedditComment]


class RedditClient:
    def __init__(
        self,
        user_agent: str,
        client_id: str | None = None,
        client_secret: str | None = None,
        *,
        timeout_seconds: float = 20.0,
        http: httpx.AsyncClient | None = None,
    ) -> None:
        # Reddit blocks requests with generic user agents like "python-httpx".
        if not user_agent:
            raise ValueError('REDDIT_USER_AGENT is not set, e.g. "web:myarc:v0.1 (by /u/your_username)".')
        self._credentials = (client_id, client_secret) if client_id and client_secret else None
        self._http = http or httpx.AsyncClient(timeout=timeout_seconds, headers={"User-Agent": user_agent})
        self._token: str | None = None
        self._token_expires_at = 0.0
        self._token_lock = asyncio.Lock()

    @property
    def uses_oauth(self) -> bool:
        return self._credentials is not None

    async def search(self, subreddit: str, query: str, *, limit: int = 10) -> list[RedditPost]:
        """Search one subreddit's threads, most relevant first."""
        listing = await self._get(
            f"/r/{subreddit}/search",
            {"q": query, "restrict_sr": "1", "sort": "relevance", "t": "all", "type": "link", "limit": str(limit)},
        )
        return [_parse_post(child["data"]) for child in listing["data"]["children"] if child.get("kind") == "t3"]

    async def read_thread(self, post_id: str, *, max_comments: int = 60) -> RedditThread:
        """Fetch a post and up to `max_comments` comments (top-voted first, 3 levels of replies)."""
        post_listing, comment_listing = await self._get(
            f"/comments/{post_id}",
            {"sort": "top", "limit": str(max_comments), "depth": "3"},
        )
        post_data = post_listing["data"]["children"][0]["data"]
        comments = list(_walk_comments(comment_listing["data"]["children"], depth=0))
        return RedditThread(
            post=_parse_post(post_data),
            body=(post_data.get("selftext") or "").strip(),
            comments=comments[:max_comments],
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _get(self, path: str, params: dict[str, str]) -> Any:
        if self.uses_oauth:
            url = OAUTH_BASE + path
            headers = {"Authorization": f"Bearer {await self._access_token()}"}
        else:
            url = PUBLIC_BASE + path + ".json"
            headers = {}

        try:
            # raw_json=1: return "&" instead of the legacy HTML-escaped "&amp;"
            response = await self._http.get(url, params={**params, "raw_json": "1"}, headers=headers)
        except httpx.HTTPError as exc:
            raise RedditClientError(f"Request to {path} failed: {exc}") from exc

        if response.status_code == 429:
            raise RedditClientError(f"Reddit rate limit hit on {path}. Slow down or use OAuth credentials.")
        if response.status_code != 200:
            raise RedditClientError(f"Reddit returned HTTP {response.status_code} for {path}.")
        return response.json()

    async def _access_token(self) -> str:
        """App-only OAuth token, fetched once and reused until shortly before it expires."""
        async with self._token_lock:
            if self._token and time.monotonic() < self._token_expires_at:
                return self._token
            try:
                response = await self._http.post(
                    TOKEN_URL,
                    auth=self._credentials,
                    data={"grant_type": "client_credentials"},
                )
            except httpx.HTTPError as exc:
                raise RedditClientError(f"Could not reach Reddit for a token: {exc}") from exc
            if response.status_code != 200:
                raise RedditClientError(
                    f"Reddit refused the token request (HTTP {response.status_code}). "
                    "Check REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET."
                )
            payload = response.json()
            self._token = payload["access_token"]
            self._token_expires_at = time.monotonic() + float(payload.get("expires_in", 3600)) - 60
            return self._token


def _parse_post(data: dict[str, Any]) -> RedditPost:
    return RedditPost(
        id=data["id"],
        title=data.get("title", ""),
        url=PUBLIC_BASE + data["permalink"].rstrip("/"),
        created_at=_utc(data["created_utc"]),
        score=int(data.get("score", 0)),
        num_comments=int(data.get("num_comments", 0)),
    )


def _walk_comments(children: list[dict[str, Any]], depth: int) -> Iterator[RedditComment]:
    """
    Flatten the comment tree depth-first, keeping Reddit's top-first order.
    """
    for child in children:
        if child.get("kind") != "t1":
            continue
        data = child["data"]
        body = (data.get("body") or "").strip()
        if body and body not in _REMOVED_BODIES:
            yield RedditComment(
                body=body,
                score=int(data.get("score", 0)),
                created_at=_utc(data["created_utc"]),
                depth=depth,
            )
        replies = data.get("replies")
        if isinstance(replies, dict):  # Reddit sends "" when there are no replies
            yield from _walk_comments(replies["data"]["children"], depth + 1)


def _utc(timestamp: float | int | str) -> datetime:
    return datetime.fromtimestamp(float(timestamp), tz=UTC)

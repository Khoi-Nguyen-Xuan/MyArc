"""Run the research agent on one course against the REAL Tavily and OpenAI APIs.

Run from the backend/ folder:
    python -m scripts.research "CMPUT 301"
    python -m scripts.research "CMPUT 301" --professor "Jane Doe" --title "Intro to Software Engineering"
    python -m scripts.research "CMPUT 301" --json out.json     # also save the raw result

Needs OPENAI_API_KEY and TAVILY_API_KEY in backend/.env. With REDDIT_USER_AGENT,
REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET too, Reddit threads come from the Reddit API
instead of Tavily. Costs a few cents per run, mostly the LLM calls.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

from app.agents.research.graph import run_research
from app.agents.research.schemas import ResearchRequest, ResearchResult, Signal
from app.agents.research.sources import build_reddit_source
from app.agents.research.state import ResearchContext
from app.external.llm_client import DEFAULT_MODEL, create_chat_model
from app.external.search_client import SearchClient

SIGNAL_MARKS = {Signal.HARDER: "▲ harder", Signal.EASIER: "▼ easier", Signal.NEUTRAL: "● neutral"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Research one course on the web.")
    parser.add_argument("course_code", help='e.g. "CMPUT 301"')
    parser.add_argument("--professor", help="the professor teaching the student's section")
    parser.add_argument("--title", help='course title, e.g. "Intro to Software Engineering"')
    parser.add_argument("--university", default="University of Alberta")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"default: {DEFAULT_MODEL}")
    parser.add_argument("--json", type=Path, help="also write the full result to this file")
    return parser.parse_args()


def require_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        sys.exit(f"{name} is missing. Add it to backend/.env and try again.")
    return value


def print_report(result: ResearchResult) -> None:
    print(f"\n=== {result.request.course_code}: {len(result.claims)} claims from {len(result.sources)} sources ===")

    print("\nSearches run:")
    for query in result.queries_run:
        print(f"  - {query}")

    print("\nSources:")
    number_of = {str(source.url): number for number, source in enumerate(result.sources, start=1)}
    for number, source in enumerate(result.sources, start=1):
        published = source.published_at or "undated"
        print(f"  [{number}] {source.source_type.value:<16} {published!s:<10}  {source.title[:70]}")
        print(f"       {source.url}")

    by_aspect = defaultdict(list)
    for claim in result.claims:
        by_aspect[claim.aspect].append(claim)

    for aspect, claims in sorted(by_aspect.items(), key=lambda item: -len(item[1])):
        print(f"\n{aspect.value} ({len(claims)})")
        for claim in claims:
            where = number_of[str(claim.source_url)]
            prof = f", prof: {claim.professor_match.value}" if result.request.professor else ""
            print(f"  {SIGNAL_MARKS[claim.signal]:<10} {claim.claim}  [{where}] (rel {claim.relevance:.1f}{prof})")
            if claim.quote:
                print(f'             "{claim.quote}"')

    harder = sum(claim.signal is Signal.HARDER for claim in result.claims)
    easier = sum(claim.signal is Signal.EASIER for claim in result.claims)
    print(f"\nOverall signal: {harder} harder, {easier} easier, {len(result.claims) - harder - easier} neutral\n")


async def main() -> None:
    load_dotenv()
    args = parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
    for noisy in ("httpx", "openai", "langchain"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    require_env("OPENAI_API_KEY")  # read by the OpenAI client itself; checked here for a clear error
    search = SearchClient(require_env("TAVILY_API_KEY"))
    reddit = build_reddit_source(
        search,
        user_agent=os.environ.get("REDDIT_USER_AGENT"),
        client_id=os.environ.get("REDDIT_CLIENT_ID"),
        client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
    )
    logging.info("Reddit threads via: %s", reddit.name)
    context = ResearchContext(search=search, llm=create_chat_model(args.model), reddit=reddit)
    request = ResearchRequest(
        course_code=args.course_code,
        professor=args.professor,
        course_title=args.title,
        university=args.university,
    )

    result = await run_research(request, context)
    print_report(result)

    if args.json:
        args.json.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        print(f"Saved full result to {args.json}")


if __name__ == "__main__":
    asyncio.run(main())

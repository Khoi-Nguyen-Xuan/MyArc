"""Run the syllabus agent on one file against the REAL OpenAI API.

Run from the backend/ folder:

    python -m scripts.syllabus tests/fixtures/syllabi/<file> --course "BIOIN 301" --term "Fall 2026"
    python -m scripts.syllabus <file> --course "CMPUT 201" --json out.json    # also save the raw result

"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from app.agents.syllabus.agent import run_syllabus_agent
from app.agents.syllabus.schemas import SyllabusRequest, SyllabusResult
from app.external.llm_client import DEFAULT_MODEL, create_chat_model
from app.utils.documents import DocumentError, load_document

LLM_TIMEOUT_SECONDS = 180  


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract assessments, dates and policies from one syllabus.")
    parser.add_argument("file", type=Path, help="a PDF or .docx syllabus")
    parser.add_argument("--course", required=True, help='the course code the student is taking, e.g. "BIOIN 301"')
    parser.add_argument("--term", help='the student\'s term, e.g. "Fall 2026"')
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"default: {DEFAULT_MODEL}")
    parser.add_argument("--json", type=Path, help="also write the full result to this file")
    return parser.parse_args()


def print_report(result: SyllabusResult) -> None:
    title = f" - {result.course_title}" if result.course_title else ""
    print(f"\n=== {result.request.course_code}{title} ({result.term or 'term not stated'}) ===")
    print(f"Instructors: {', '.join(result.instructors) or 'not found'}")

    print("\nAssessments:")
    for assessment in result.assessments:
        weight = f"{assessment.count} x {assessment.weight_each:g}%" if assessment.count > 1 else ""
        total = f"{assessment.total_weight:g}%"
        dates = ", ".join(day.strftime("%b %d") for day in assessment.due_dates) or "no dates"
        print(f"  {assessment.name:<24} {assessment.kind.value:<13} {weight:>9} = {total:>5}   {dates}")
        if assessment.notes:
            print(f"  {'':<24} note: {assessment.notes}")
        print(f'  {"":<24} source: {_where(assessment.source.page)}"{assessment.source.quote}"')

    extra = f"  (includes {result.extra_credit:g}% extra credit)" if result.extra_credit else ""
    print(f"  {'Total':<24} {'':<13} {'':>9}   {result.total_weight:>4g}%{extra}")

    print("\nPolicies:")
    for policy in result.policies:
        print(f"  {policy.topic.value:<14} {policy.summary}  ({_where(policy.source.page).strip() or 'no page'})")
    if not result.policies:
        print("  none found")

    print("\nWarnings:")
    for warning in result.warnings:
        print(f"  - {warning}")
    if not result.warnings:
        print("  none")
    print()


def _where(page: int | None) -> str:
    return f"p.{page} " if page else ""


async def main() -> None:
    load_dotenv()
    args = parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
    for noisy in ("httpx", "openai", "langchain"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY is missing. Add it to backend/.env and try again.")
    if not args.file.is_file():
        sys.exit(f"No such file: {args.file}")

    try:
        document = load_document(args.file.read_bytes(), args.file.name)
    except DocumentError as exc:
        sys.exit(f"Can't read {args.file.name}: {exc}")

    characters = len(document.full_text())
    logging.info("Read %s (%d characters). Asking the LLM, about 30-90s...", document.file_name, characters)
    llm = create_chat_model(args.model, timeout_seconds=LLM_TIMEOUT_SECONDS)
    result = await run_syllabus_agent(llm, SyllabusRequest(course_code=args.course, term=args.term), document)
    print_report(result)

    if args.json:
        args.json.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        print(f"Saved full result to {args.json}")


if __name__ == "__main__":
    asyncio.run(main())

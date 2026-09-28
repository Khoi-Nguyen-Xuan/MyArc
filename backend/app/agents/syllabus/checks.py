"""Checks on an extracted syllabus that need no LLM.

Each check describes what's wrong in plain words. The agent sends those
problems back to the LLM for one repair; whatever is still wrong afterwards
is shown to the student as a warning.

Quotes that can't be matched are the exception: they are only noted, never
repaired. PDF text often breaks spacing ("asChatGPT") or splits table cells,
so an honest quote can fail to match, and re-reading the whole syllabus for
that cost ~20s while rarely changing the facts.

One check also corrects something itself: page numbers come from where each
quote is actually found in the document, not from the LLM.
"""

from __future__ import annotations

import re
from datetime import date

from app.agents.syllabus.schemas import SourceRef, SyllabusResult
from app.utils.documents import Document

# When each term runs, with some slack for early starts and final exams:
# first day, last day, and which year of an academic year like "2026-2027" it falls in.
_TERMS = {
    "fall": ((8, 15), (12, 31), "first"),
    "winter": ((1, 1), (4, 30), "last"),
    "spring": ((4, 25), (6, 30), "last"),
    "summer": ((6, 25), (8, 31), "last"),
}

_YEAR = re.compile(r"\b20\d{2}\b")
_ELLIPSIS = re.compile(r"\.\.\.|…")
_TYPOGRAPHY = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", "|": " "})


def check_result(result: SyllabusResult, document: Document) -> tuple[SyllabusResult, list[str], list[str]]:
    """Run every check.

    Returns the result with verified page numbers, the problems worth a repair
    (weights, dates), and notes about quotes that couldn't be matched.
    """
    result, quote_notes = _verify_quotes(result, document)
    problems = _check_weights(result) + _check_dates(result)
    return result, problems, quote_notes


def term_window(term: str | None) -> tuple[date, date] | None:
    """Turn "Fall 2026" into (2026-08-15, 2026-12-31); "Winter Term 2026-2027" falls in 2027. None if unreadable."""
    if not term:
        return None
    text = term.lower()
    season = next((name for name in _TERMS if name in text), None)
    years = [int(year) for year in _YEAR.findall(text)]
    if season is None or not years:
        return None

    (start_month, start_day), (end_month, end_day), which_year = _TERMS[season]
    year = years[0] if which_year == "first" else years[-1]
    return date(year, start_month, start_day), date(year, end_month, end_day)


def _verify_quotes(result: SyllabusResult, document: Document) -> tuple[SyllabusResult, list[str]]:
    """Find every quote in the document. Found: take its page from there. Not found: note it."""
    parts = [(part.page, _squash(part.text)) for part in document.parts]
    whole = _squash(" ".join(part.text for part in document.parts))  # for quotes that cross a page break
    notes: list[str] = []

    def verify(label: str, source: SourceRef) -> SourceRef:
        found, page = _locate(source.quote, parts, whole)
        if not found:
            notes.append(f"The quote for {label} couldn't be matched exactly in the syllabus text.")
            return source
        return source.model_copy(update={"page": page})

    assessments = [
        assessment.model_copy(update={"source": verify(f'"{assessment.name}"', assessment.source)})
        for assessment in result.assessments
    ]
    policies = [
        policy.model_copy(update={"source": verify(f"the {policy.topic.value} policy", policy.source)})
        for policy in result.policies
    ]
    return result.model_copy(update={"assessments": assessments, "policies": policies}), notes


def _locate(quote: str, parts: list[tuple[int | None, str]], whole: str) -> tuple[bool, int | None]:
    """Is the quote in the document, and on which page? A quote shortened with "..." matches piece by piece.

    Tried on each page first (to get the page number), then on the whole document,
    for a quote that runs across a page break (found, but the page is unknown).
    """
    pieces = [piece for piece in (_squash(piece) for piece in _ELLIPSIS.split(quote)) if piece]
    if not pieces:
        return False, None
    for page, text in parts:
        if all(piece in text for piece in pieces):
            return True, page
    if all(piece in whole for piece in pieces):
        return True, None
    return False, None


def _squash(text: str) -> str:
    """Ignore case, ALL whitespace, curly quotes, long dashes and table separators when comparing.

    Whitespace is removed entirely, not just collapsed: PDF text often drops or
    adds spaces at line wraps ("such asChatGPT"), which would fail an exact match.
    """
    return "".join(text.translate(_TYPOGRAPHY).lower().split())


def _check_weights(result: SyllabusResult) -> list[str]:
    """Under 100% usually means an assessment was missed. Over 100% is extra credit, which is fine."""
    if not result.assessments:
        return ["No graded assessments were found."]
    total = round(result.total_weight, 1)
    if total < 100:
        return [f"Weights add up to {total:g}%, not 100%; an assessment may be missing."]
    return []


def _check_dates(result: SyllabusResult) -> list[str]:
    """A date outside the term is usually the wrong year. The student's own term wins over the syllabus's."""
    term = result.request.term or result.term
    window = term_window(term)
    if window is None:
        return []
    start, end = window
    return [
        f'"{assessment.name}" has a date ({day.isoformat()}) outside the {term} term.'
        for assessment in result.assessments
        for day in assessment.due_dates
        if not start <= day <= end
    ]

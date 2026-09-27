"""Reads a whole syllabus and turns the answer into a `SyllabusResult`.

The full text goes to the LLM, not retrieved chunks: a syllabus is 5-15k
tokens, and extraction has to see every row of the grading table.

The split of work:

- the LLM reads the document: which assessments exist, their weights and dates;
- the code checks the answer's shape: parses dates, applies the contract's
  rules, and records anything it can't use as a warning instead of failing.
"""

from __future__ import annotations

from datetime import date
from functools import cache
from pathlib import Path

from langchain.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

from app.agents.syllabus.schemas import (
    Assessment,
    AssessmentKind,
    Policy,
    PolicyTopic,
    SourceRef,
    SyllabusRequest,
    SyllabusResult,
)
from app.core.course_codes import normalize_course_code
from app.utils.documents import Document

PROMPT_PATH = Path(__file__).parents[1] / "prompts" / "syllabus_agent.md"


# What the LLM returns
class ExtractedSource(BaseModel):
    quote: str
    page: int | None


class ExtractedAssessment(BaseModel):
    name: str
    kind: AssessmentKind
    count: int
    weight_each: float
    due_dates: list[str]  # YYYY-MM-DD, parsed by our code
    notes: str | None
    source: ExtractedSource


class ExtractedPolicy(BaseModel):
    topic: PolicyTopic
    summary: str
    source: ExtractedSource


class SyllabusExtraction(BaseModel):
    course_code: str | None
    course_title: str | None
    term: str | None
    instructors: list[str]
    assessments: list[ExtractedAssessment]
    policies: list[ExtractedPolicy]


async def ask_for_extraction(
    llm: BaseChatModel,
    request: SyllabusRequest,
    document: Document,
    *,
    previous: SyllabusExtraction | None = None,
    problems: list[str] | None = None,
) -> SyllabusExtraction:
    """Ask the LLM to read the syllabus.

    For a repair, pass its `previous` answer and the `problems` our checks found:
    the LLM then sees the same syllabus, its own answer, and what to fix.
    """
    messages = build_messages(request, document)
    if previous is not None:
        messages += [AIMessage(previous.model_dump_json()), HumanMessage(_repair_request(problems or []))]
    extractor = llm.with_structured_output(SyllabusExtraction)
    return await extractor.ainvoke(messages)


def build_messages(request: SyllabusRequest, document: Document) -> list[BaseMessage]:
    header = "\n".join(
        [
            f"Course code: {request.course_code or 'not given, use the code the syllabus names'}",
            f"Student's term: {request.term or 'not given'}",
            f"File: {document.file_name}",
        ]
    )
    user_message = f"{header}\n\n<syllabus>\n{document.full_text()}\n</syllabus>"
    return [SystemMessage(_system_prompt()), HumanMessage(user_message)]


def _repair_request(problems: list[str]) -> str:
    listed = "\n".join(f"- {problem}" for problem in problems)
    return (
        f"Your answer has these problems:\n{listed}\n\n"
        "Fix them using the syllabus above and return the complete corrected answer, "
        "including the parts that were already right. If something really isn't in the syllabus, "
        "leave it out instead of guessing."
    )


def to_result(
    extraction: SyllabusExtraction,
    request: SyllabusRequest,
    *,
    has_pages: bool,
) -> tuple[SyllabusResult, list[str]]:
    """Convert the LLM's answer into the contract.

    An assessment or date that breaks the contract is left out and reported as
    a problem, instead of failing the whole answer.
    """
    problems: list[str] = []
    assessments: list[Assessment] = []

    for item in extraction.assessments:
        due_dates: set[date] = set()
        for text in item.due_dates:
            parsed = _parse_date(text)
            if parsed is None:
                problems.append(f'Ignored an unreadable date "{text}" for "{item.name}".')
            else:
                due_dates.add(parsed)
        try:
            assessments.append(
                Assessment(
                    name=item.name.strip(),
                    kind=item.kind,
                    count=item.count,
                    weight_each=item.weight_each,
                    due_dates=sorted(due_dates),
                    notes=(item.notes or "").strip() or None,
                    source=_to_source(item.source, has_pages),
                )
            )
        except ValidationError as exc:
            problems.append(f'Left out "{item.name}": {_describe(exc)}.')

    policies = [
        Policy(topic=item.topic, summary=item.summary.strip(), source=_to_source(item.source, has_pages))
        for item in extraction.policies
        if item.summary.strip()
    ]

    course_code = request.course_code or _clean(extraction.course_code)
    if course_code is None:
        problems.append("No course code was found in the syllabus.")
    else:
        request = request.model_copy(update={"course_code": normalize_course_code(course_code)})

    result = SyllabusResult(
        request=request,
        course_title=_clean(extraction.course_title),
        term=_clean(extraction.term),
        instructors=[name.strip() for name in extraction.instructors if name.strip()],
        assessments=assessments,
        policies=policies,
    )
    return result, problems


def _to_source(source: ExtractedSource, has_pages: bool) -> SourceRef:
    """Collapse the layout's column spacing in the quote. Word documents have no pages, so any page is dropped."""
    page = source.page if has_pages and source.page and source.page >= 1 else None
    return SourceRef(quote=" ".join(source.quote.split()), page=page)


def _describe(exc: ValidationError) -> str:
    """The first problem, readable: "weight_each: Input should be greater than 0"."""
    problem = exc.errors()[0]
    message = problem["msg"].removeprefix("Value error, ").rstrip(".")
    field = ".".join(str(part) for part in problem["loc"])
    return f"{field}: {message}" if field else message


def _parse_date(text: str) -> date | None:
    try:
        return date.fromisoformat(text.strip())
    except ValueError:
        return None


def _clean(text: str | None) -> str | None:
    return (text or "").strip() or None


@cache
def _system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")

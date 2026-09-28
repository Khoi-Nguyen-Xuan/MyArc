"""Runs the agents on one uploaded syllabus.

When the student typed the course code, research doesn't need the syllabus,
so the two run at the same time:

    file -> syllabus agent --+
                             +-> evaluator -> CourseAnalysis
    code -> research agent --+

Without a typed code, research waits for the code the syllabus agent finds:

    file -> syllabus agent -> research agent -> evaluator -> CourseAnalysis
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from langchain.chat_models import BaseChatModel

from app.agents.evaluator.agent import evaluate_course
from app.agents.evaluator.schemas import CourseEvaluation
from app.agents.research.graph import run_research
from app.agents.research.schemas import ResearchRequest, ResearchResult
from app.agents.research.sources import build_reddit_source
from app.agents.research.state import ResearchContext
from app.agents.syllabus.agent import run_syllabus_agent
from app.agents.syllabus.schemas import SyllabusRequest, SyllabusResult
from app.config import settings
from app.core.timing import StageTimer
from app.external.llm_client import create_chat_model
from app.external.search_client import SearchClient, SearchClientError
from app.utils.documents import load_document

logger = logging.getLogger(__name__)

LLM_TIMEOUT_SECONDS = 180  # a long syllabus takes the LLM a while to read


class AnalysisError(Exception):
    """The syllabus can't be analyzed. The message is written to be shown to the users."""


class SetupError(Exception):
    """The server is missing an API key"""


@dataclass(frozen=True, slots=True)
class CourseAnalysis:
    syllabus: SyllabusResult
    research: ResearchResult
    evaluation: CourseEvaluation


async def analyze_syllabus(
    data: bytes,
    file_name: str,
    *,
    course_code: str | None = None,
    term: str | None = None,
) -> CourseAnalysis:
    """Analyze one course. Raises DocumentError or AnalysisError (student's file), SetupError (server)."""
    _require_keys()
    timer = StageTimer(file_name)
    with timer.stage("load document"):
        document = load_document(data, file_name)
    llm = create_chat_model(
        settings.llm_model,
        api_key=settings.openai_api_key,
        timeout_seconds=LLM_TIMEOUT_SECONDS,
        reasoning_effort=settings.llm_reasoning_effort,
    )

    syllabus_request = SyllabusRequest(course_code=course_code, term=term)

    async def read_syllabus() -> SyllabusResult:
        logger.info("Reading syllabus %s", file_name)
        with timer.stage("syllabus agent"):
            return await run_syllabus_agent(llm, syllabus_request, document)

    async def research(request: ResearchRequest) -> tuple[ResearchResult, list[str]]:
        logger.info("Researching %s", request.course_code)
        with timer.stage("research agent"):
            return await _research(llm, request)

    if syllabus_request.course_code:
        # typed code: both at once. The TaskGroup cancels research if the syllabus fails.
        # Research only knows the code and term here (no title or professor from the syllabus).
        typed = ResearchRequest(course_code=syllabus_request.course_code, term=syllabus_request.term)
        with timer.stage("syllabus + research (parallel)"):
            try:
                async with asyncio.TaskGroup() as group:
                    syllabus_task = group.create_task(read_syllabus())
                    research_task = group.create_task(research(typed))
            except ExceptionGroup as failed:
                # re-raise the real error (DocumentError, AnalysisError, ...) so the
                # endpoint can still turn it into the right message for the student
                raise failed.exceptions[0] from None
        syllabus = syllabus_task.result()
        research_result, research_warnings = research_task.result()
    else:
        syllabus = await read_syllabus()
        if not syllabus.request.course_code:
            raise AnalysisError("We couldn't find the course code in this syllabus. Please enter it and upload again.")
        research_result, research_warnings = await research(_research_request(syllabus))

    logger.info("Evaluating %s", syllabus.request.course_code)
    with timer.stage("evaluator"):
        evaluation = await evaluate_course(llm, syllabus, research_result)
    logger.info(timer.summary())
    if research_warnings:
        evaluation = evaluation.model_copy(update={"warnings": [*evaluation.warnings, *research_warnings]})
    return CourseAnalysis(syllabus=syllabus, research=research_result, evaluation=evaluation)


def _research_request(syllabus: SyllabusResult) -> ResearchRequest:
    """Research what the syllabus agent found: code, title and (when unambiguous) the professor."""
    return ResearchRequest(
        course_code=syllabus.request.course_code,
        course_title=syllabus.course_title,
        # Only search a professor's name when we know it's the student's; a list could be all sections.
        professor=syllabus.instructors[0] if len(syllabus.instructors) == 1 else None,
        term=syllabus.term or syllabus.request.term,
    )


async def _research(llm: BaseChatModel, request: ResearchRequest) -> tuple[ResearchResult, list[str]]:
    """What students say about the course. A search outage gives an empty result, not a failed upload."""
    search = SearchClient(settings.tavily_api_key)
    reddit = build_reddit_source(
        search,
        user_agent=settings.reddit_user_agent,
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
    )
    try:
        return await run_research(request, ResearchContext(search=search, llm=llm, reddit=reddit)), []
    except SearchClientError as exc:
        logger.warning("Research failed for %s: %s", request.course_code, exc)
        return ResearchResult(request=request), ["Student reviews couldn't be searched right now, so they aren't included."]
    finally:
        await reddit.aclose()


def _require_keys() -> None:
    missing = [name for name, value in (("OPENAI_API_KEY", settings.openai_api_key), ("TAVILY_API_KEY", settings.tavily_api_key)) if not value]
    if missing:
        raise SetupError(f"The server is missing {' and '.join(missing)} in backend/.env.")

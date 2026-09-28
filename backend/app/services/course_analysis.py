"""Runs the agents on one uploaded syllabus:

    file -> syllabus agent -> research agent -> evaluator -> CourseAnalysis
"""

from __future__ import annotations

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
    llm = create_chat_model(settings.llm_model, api_key=settings.openai_api_key, timeout_seconds=LLM_TIMEOUT_SECONDS)

    logger.info("Reading syllabus %s", file_name)
    with timer.stage("syllabus agent"):
        syllabus = await run_syllabus_agent(llm, SyllabusRequest(course_code=course_code, term=term), document)
    if not syllabus.request.course_code:
        raise AnalysisError("We couldn't find the course code in this syllabus. Please enter it and upload again.")

    logger.info("Researching %s", syllabus.request.course_code)
    with timer.stage("research agent"):
        research, research_warnings = await _research(llm, syllabus)

    logger.info("Evaluating %s", syllabus.request.course_code)
    with timer.stage("evaluator"):
        evaluation = await evaluate_course(llm, syllabus, research)
    logger.info(timer.summary())
    if research_warnings:
        evaluation = evaluation.model_copy(update={"warnings": [*evaluation.warnings, *research_warnings]})
    return CourseAnalysis(syllabus=syllabus, research=research, evaluation=evaluation)


async def _research(llm: BaseChatModel, syllabus: SyllabusResult) -> tuple[ResearchResult, list[str]]:
    """What students say about the course. A search outage gives an empty result, not a failed upload."""
    request = ResearchRequest(
        course_code=syllabus.request.course_code,
        course_title=syllabus.course_title,
        # Only search a professor's name when we know it's the student's; a list could be all sections.
        professor=syllabus.instructors[0] if len(syllabus.instructors) == 1 else None,
        term=syllabus.term or syllabus.request.term,
    )
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

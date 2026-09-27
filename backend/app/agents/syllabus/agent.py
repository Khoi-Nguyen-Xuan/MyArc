"""The syllabus agent: read a syllabus, check the answer, and repair it once if needed.

    ask the LLM -> convert and check -> any problems? -> ask again with the problems listed
                                                      -> keep whichever answer has fewer problems

A plain function rather than a LangGraph graph: it's a straight line with one retry.
"""

from __future__ import annotations

import logging

from langchain.chat_models import BaseChatModel

from app.agents.syllabus.checks import check_result
from app.agents.syllabus.extraction import SyllabusExtraction, ask_for_extraction, to_result
from app.agents.syllabus.schemas import SyllabusRequest, SyllabusResult
from app.external.llm_client import is_setup_error
from app.utils.documents import Document

logger = logging.getLogger(__name__)


async def run_syllabus_agent(llm: BaseChatModel, request: SyllabusRequest, document: Document) -> SyllabusResult:
    """Extract the course facts from one syllabus. Problems still left at the end become `result.warnings`."""
    extraction = await ask_for_extraction(llm, request, document)
    result, problems = _review(extraction, request, document)

    if problems:
        logger.info("%s: %d problem(s), asking for one repair: %s", document.file_name, len(problems), problems)
        try:
            repaired = await ask_for_extraction(llm, request, document, previous=extraction, problems=problems)
        except Exception as exc:
            if is_setup_error(exc):
                raise
            logger.warning("Repair failed, keeping the first answer: %s: %s", type(exc).__name__, exc)
        else:
            repaired_result, repaired_problems = _review(repaired, request, document)
            if len(repaired_problems) < len(problems):
                result, problems = repaired_result, repaired_problems

    return result.model_copy(update={"warnings": problems})


def _review(
    extraction: SyllabusExtraction,
    request: SyllabusRequest,
    document: Document,
) -> tuple[SyllabusResult, list[str]]:
    """Convert the LLM's answer, then check it. Returns the result and every problem found."""
    result, conversion_problems = to_result(extraction, request, has_pages=any(part.page for part in document.parts))
    result, check_problems = check_result(result, document)
    return result, conversion_problems + check_problems

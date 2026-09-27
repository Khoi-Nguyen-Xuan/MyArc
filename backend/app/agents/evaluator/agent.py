"""The evaluator agent: scores one course from its syllabus and what students say.

    code scores 3 criteria + confidence -> LLM judges the other 3 -> CourseEvaluation
                                                                      (point and ranking computed)
"""

from __future__ import annotations

from langchain.chat_models import BaseChatModel

from app.agents.evaluator.judgment import ask_for_judgment, build_facts, to_scores
from app.agents.evaluator.schemas import CourseEvaluation
from app.agents.evaluator.scoring import assessment_weighting, confidence, deadline_pressure, student_review_difficulty
from app.agents.research.schemas import ResearchResult
from app.agents.syllabus.schemas import SyllabusResult


async def evaluate_course(llm: BaseChatModel, syllabus: SyllabusResult, research: ResearchResult) -> CourseEvaluation:
    computed = [deadline_pressure(syllabus), assessment_weighting(syllabus), student_review_difficulty(research)]
    facts = build_facts(syllabus, research, computed)
    judgment = await ask_for_judgment(llm, facts)
    judged, weekly_hours = to_scores(judgment, facts)
    trust, reasons = confidence(syllabus, research)

    return CourseEvaluation(
        course_code=syllabus.request.course_code or "",
        criteria=judged + computed,
        weekly_hours=weekly_hours,
        confidence=trust,
        short_review=judgment.short_review.strip(),
        summary=judgment.summary.strip(),
        warnings=[*syllabus.warnings, *reasons],
    )

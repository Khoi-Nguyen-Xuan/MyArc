"""The evaluator's LLM part: scores the three criteria that need judgment.

The LLM reads the syllabus facts and student claims as numbered lines ([S3],
[R7]) and cites them by id. Our code turns the ids back into evidence, so every
piece of evidence in the result is a real syllabus fact or student claim, never
text the LLM wrote.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path

from langchain.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from app.agents.evaluator.schemas import Criterion, CriterionScore, EvidenceItem, ScoredBy, WeeklyHours
from app.agents.evaluator.scoring import student_evidence, syllabus_evidence
from app.agents.research.schemas import ResearchResult
from app.agents.syllabus.schemas import SyllabusResult

PROMPT_PATH = Path(__file__).parents[1] / "prompts" / "evaluator.md"

MAX_STUDENT_CLAIMS = 40  # the most relevant ones; keeps the prompt small and focused


# What the LLM returns. No defaults, as OpenAI's strict structured output requires;
# scores and hours are clamped to their ranges in code.
class JudgedCriterion(BaseModel):
    score: float
    reasoning: str
    evidence_ids: list[str]


class Judgment(BaseModel):
    workload: JudgedCriterion
    conceptual_difficulty: JudgedCriterion
    continuous_study: JudgedCriterion
    weekly_hours_min: int
    weekly_hours_max: int
    short_review: str
    summary: str


@dataclass(frozen=True, slots=True)
class Facts:
    """What the LLM reads, and the evidence behind each numbered line."""

    text: str
    evidence: dict[str, EvidenceItem]  # "S3" -> the syllabus fact, "R7" -> the student claim


def build_facts(syllabus: SyllabusResult, research: ResearchResult, computed: list[CriterionScore]) -> Facts:
    evidence: dict[str, EvidenceItem] = {}
    title = f" - {syllabus.course_title}" if syllabus.course_title else ""
    lines = [f"Course: {syllabus.request.course_code}{title} ({syllabus.term or syllabus.request.term or 'term unknown'})"]

    lines += ["", "Syllabus facts:"]
    for assessment in syllabus.assessments:
        fact_id = f"S{len(evidence) + 1}"
        evidence[fact_id] = syllabus_evidence(assessment)
        dates = ", ".join(day.isoformat() for day in assessment.due_dates) or "no dates given"
        notes = f"; {assessment.notes}" if assessment.notes else ""
        lines.append(f"[{fact_id}] {evidence[fact_id].text} ({assessment.kind.value}), {dates}{notes}")
    for policy in syllabus.policies:
        fact_id = f"S{len(evidence) + 1}"
        evidence[fact_id] = EvidenceItem(text=policy.summary, quote=policy.source.quote, page=policy.source.page)
        lines.append(f"[{fact_id}] Policy ({policy.topic.value}): {policy.summary}")
    if not syllabus.assessments and not syllabus.policies:
        lines.append("(none found)")

    lines += ["", "Scores our code computed from these facts (0-100):"]
    lines += [f"- {score.criterion.value}: {score.score:g}. {score.reasoning}" for score in computed]

    lines += ["", "Student claims from Reddit:"]
    posted = {str(source.url): source.published_at for source in research.sources}
    claims = sorted(research.claims, key=lambda claim: claim.relevance, reverse=True)[:MAX_STUDENT_CLAIMS]
    for number, claim in enumerate(claims, start=1):
        fact_id = f"R{number}"
        evidence[fact_id] = student_evidence(claim)
        date = posted.get(str(claim.source_url))
        when = f", posted {date:%Y-%m}" if date else ""
        lines.append(f"[{fact_id}] ({claim.aspect.value}, {claim.signal.value}, relevance {claim.relevance:.1f}{when}) {claim.claim}")
    if not claims:
        lines.append("(none found)")

    return Facts(text="\n".join(lines), evidence=evidence)


async def ask_for_judgment(llm: BaseChatModel, facts: Facts) -> Judgment:
    judge = llm.with_structured_output(Judgment)
    return await judge.ainvoke([SystemMessage(_system_prompt()), HumanMessage(facts.text)])


def to_scores(judgment: Judgment, facts: Facts) -> tuple[list[CriterionScore], WeeklyHours]:
    """Convert the LLM's answer: clamp numbers to their ranges and resolve cited ids to evidence."""
    scores = [
        _to_score(Criterion.WORKLOAD, judgment.workload, facts),
        _to_score(Criterion.CONCEPTUAL_DIFFICULTY, judgment.conceptual_difficulty, facts),
        _to_score(Criterion.CONTINUOUS_STUDY, judgment.continuous_study, facts),
    ]
    low, high = sorted(_clamp(hours, 0, 60) for hours in (judgment.weekly_hours_min, judgment.weekly_hours_max))
    return scores, WeeklyHours(min=int(low), max=int(high))


def _to_score(criterion: Criterion, judged: JudgedCriterion, facts: Facts) -> CriterionScore:
    cited = dict.fromkeys(fact_id.strip().strip("[]").upper() for fact_id in judged.evidence_ids)
    return CriterionScore(
        criterion=criterion,
        score=round(_clamp(judged.score, 0, 100), 1),
        scored_by=ScoredBy.LLM,
        reasoning=judged.reasoning.strip(),
        evidence=[facts.evidence[fact_id] for fact_id in cited if fact_id in facts.evidence],  # unknown ids dropped
    )


def _clamp(value: float, low: float, high: float) -> float:
    return min(max(value, low), high)


@cache
def _system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")

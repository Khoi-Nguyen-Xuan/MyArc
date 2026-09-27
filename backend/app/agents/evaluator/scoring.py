"""The criteria scored in code, and the evaluation's confidence.

These three criteria can be counted from the data, so no LLM is involved: the
numbers are exact, the same on every run, and easy to explain in the "Why?"
drawer. Each function returns a `CriterionScore` with its reasoning and evidence.

- deadline pressure: how many graded items the term has;
- assessment weighting: how much of the grade rides on midterms and finals;
- student review difficulty: the balance of "harder" and "easier" student claims.
"""

from __future__ import annotations

from app.agents.evaluator.schemas import Criterion, CriterionScore, EvidenceItem, ScoredBy
from app.agents.research.schemas import EvidenceClaim, ResearchResult, Signal, SourceType
from app.agents.syllabus.schemas import Assessment, AssessmentKind, SyllabusResult

# Deadline pressure: 26 graded items (two a week over a 13-week term) scores 100.
ITEMS_FOR_FULL_PRESSURE = 26

EXAM_KINDS = {AssessmentKind.MIDTERM, AssessmentKind.FINAL_EXAM}

# Student review difficulty: with fewer opinions than this (weighted by relevance),
# the score is pulled toward 50, the "no idea" middle, so two posts can't decide it.
OPINIONS_FOR_FULL_TRUST = 8
MAX_STUDENT_EVIDENCE = 6

# Confidence: how many Reddit threads with claims count as "well covered".
THREADS_FOR_FULL_COVERAGE = 5


def deadline_pressure(syllabus: SyllabusResult) -> CriterionScore:
    items = sum(assessment.count for assessment in syllabus.assessments)
    score = min(items / ITEMS_FOR_FULL_PRESSURE, 1.0) * 100
    breakdown = ", ".join(f"{assessment.count} {assessment.name}" for assessment in syllabus.assessments)
    return CriterionScore(
        criterion=Criterion.DEADLINE_PRESSURE,
        score=round(score, 1),
        scored_by=ScoredBy.CODE,
        reasoning=f"{items} graded items over the term ({breakdown or 'none found'}).",
        evidence=[syllabus_evidence(assessment) for assessment in syllabus.assessments],
    )


def assessment_weighting(syllabus: SyllabusResult) -> CriterionScore:
    """The share of the grade from midterms and finals.

    Divided by the syllabus's own total, so a course worth 104% (extra credit) is
    measured against 104, not 100.
    """
    exams = [assessment for assessment in syllabus.assessments if assessment.kind in EXAM_KINDS]
    exam_weight = sum(assessment.total_weight for assessment in exams)
    share = exam_weight / syllabus.total_weight * 100 if syllabus.total_weight else 0.0
    return CriterionScore(
        criterion=Criterion.ASSESSMENT_WEIGHTING,
        score=round(share, 1),
        scored_by=ScoredBy.CODE,
        reasoning=f"Midterms and finals make up {exam_weight:g}% of a {syllabus.total_weight:g}% grade.",
        evidence=[syllabus_evidence(assessment) for assessment in exams],
    )


def student_review_difficulty(research: ResearchResult) -> CriterionScore:
    """The relevance-weighted share of "harder" among "harder" and "easier" claims.

    Neutral claims don't count. With few opinions the score is pulled toward 50.
    """
    opinions = [claim for claim in research.claims if claim.signal is not Signal.NEUTRAL]
    harder = sum(claim.relevance for claim in opinions if claim.signal is Signal.HARDER)
    easier = sum(claim.relevance for claim in opinions if claim.signal is Signal.EASIER)
    total = harder + easier

    if total == 0:
        score, reasoning = 50.0, "No student opinions about its difficulty were found."
    else:
        raw = harder / total * 100
        trust = min(total / OPINIONS_FOR_FULL_TRUST, 1.0)
        score = 50 + (raw - 50) * trust
        reasoning = (
            f"{sum(c.signal is Signal.HARDER for c in opinions)} student claims say it is demanding and "
            f"{sum(c.signal is Signal.EASIER for c in opinions)} say it is manageable."
        )
        if trust < 1:
            reasoning += " Few opinions, so the score is pulled toward the middle."

    strongest = sorted(opinions, key=lambda claim: claim.relevance, reverse=True)[:MAX_STUDENT_EVIDENCE]
    return CriterionScore(
        criterion=Criterion.STUDENT_REVIEW_DIFFICULTY,
        score=round(score, 1),
        scored_by=ScoredBy.CODE,
        reasoning=reasoning,
        evidence=[student_evidence(claim) for claim in strongest],
    )


def confidence(syllabus: SyllabusResult, research: ResearchResult) -> tuple[float, list[str]]:
    """How much to trust the evaluation, 0-1, and the reasons it isn't higher.

    Half comes from the syllabus (fewer extraction warnings is better), half from
    student coverage (distinct Reddit threads with claims).
    """
    reasons: list[str] = []

    syllabus_quality = 1.0 - min(0.1 * len(syllabus.warnings), 0.5)
    if not syllabus.assessments:
        syllabus_quality = 0.0
        reasons.append("No graded assessments were found in the syllabus.")
    elif syllabus.warnings:
        reasons.append(f"The syllabus reading had {len(syllabus.warnings)} warning(s).")

    threads = sum(source.source_type is SourceType.REDDIT for source in research.sources)
    coverage = min(threads / THREADS_FOR_FULL_COVERAGE, 1.0)
    if threads == 0:
        reasons.append("No student threads were found; scores rely on the syllabus alone.")
    elif threads < THREADS_FOR_FULL_COVERAGE:
        reasons.append(f"Only {threads} student thread(s) found; scores lean more on the syllabus.")

    return round(0.5 * syllabus_quality + 0.5 * coverage, 2), reasons


def student_evidence(claim: EvidenceClaim) -> EvidenceItem:
    return EvidenceItem(text=claim.claim, link=claim.source_url, quote=claim.quote)


def syllabus_evidence(assessment: Assessment) -> EvidenceItem:
    weight = f"{assessment.weight_each:g}%"
    if assessment.count > 1:
        weight = f"{assessment.count} x {weight}"
    return EvidenceItem(
        text=f"{assessment.name}: {weight}",
        quote=assessment.source.quote,
        page=assessment.source.page,
    )

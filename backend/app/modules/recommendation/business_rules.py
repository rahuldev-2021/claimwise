"""Deterministic recommendation business rules."""

from app.modules.llm.schemas.llm_assessment import TechnicalAlignment
from app.modules.recommendation.schemas.context import RecommendationContext
from app.modules.recommendation.workflow_mapping import map_overall_recommendation
from app.schemas.llm_execution import LLMExecutionStatus
from app.schemas.recommendation import OverallRecommendation
from app.schemas.financial_validation import FinancialStatus
from app.schemas.technical_validation import FindingSeverity, TechnicalStatus


def apply_business_rules(
    ctx: RecommendationContext,
) -> tuple[OverallRecommendation, list[str], list[str]]:
    triggered: list[str] = []
    reasons: list[str] = []
    tv = ctx.technical

    if ctx.llm_execution.status in (LLMExecutionStatus.FAILED, LLMExecutionStatus.SKIPPED):
        triggered.append("R_LLM_UNAVAILABLE")
        reasons.append("Contextual LLM reasoning unavailable; deterministic rules applied.")

    blocking_findings = [
        f
        for f in tv.missing_evidence_findings
        if f.priority in (FindingSeverity.MATERIAL, FindingSeverity.REVIEW)
    ]
    critical_missing = bool(blocking_findings) or bool(tv.missing_evidence)
    if critical_missing:
        triggered.append("R_INSUFFICIENT_EVIDENCE")
        reasons.append("Critical diagnostic or evidence gaps identified.")

    has_contradiction = (
        bool(tv.contradictory_evidence) or tv.technical_status == TechnicalStatus.NEEDS_REVIEW
    )
    if has_contradiction:
        triggered.append("R_CONTRADICTIONS")
        reasons.append("Contradictions or review flags require human attention.")

    if ctx.llm_assessment and ctx.llm_available:
        align = ctx.llm_assessment.assessment.suggested_alignment
        if tv.technical_status == TechnicalStatus.SUPPORTED and align == TechnicalAlignment.MISALIGNED:
            triggered.append("R_LLM_DISAGREEMENT")
            reasons.append("LLM contextual view conflicts with technical validation (advisory).")
            ctx.llm_disagreement = True
        elif tv.technical_status == TechnicalStatus.NEEDS_REVIEW and align == TechnicalAlignment.ALIGNED:
            triggered.append("R_LLM_DISAGREEMENT")
            reasons.append("LLM alignment conflicts with technical validation status.")
            ctx.llm_disagreement = True

    if tv.technical_status == TechnicalStatus.INSUFFICIENT_EVIDENCE and ctx.retrieval_passage_count == 0:
        triggered.append("R_INCOMPLETE_ASSESSMENT")
        reasons.append("Insufficient information to complete assessment.")

    if ctx.financial_enabled:
        if ctx.financial is None:
            triggered.append("R_FINANCIAL_UNAVAILABLE")
            reasons.append("Financial validation was enabled but did not complete.")
        elif not ctx.financial_available or (
            ctx.financial.predicted_parts_cost is None or ctx.financial.predicted_labour_hours is None
        ):
            triggered.append("R_FINANCIAL_UNAVAILABLE")
            reasons.append("Financial ML predictions unavailable; do not assume costs are acceptable.")
        elif ctx.financial.financial_status == FinancialStatus.OUTSIDE_EXPECTED_RANGE:
            triggered.append("R_FINANCIAL_DISCREPANCY")
            reasons.append(
                "Submitted costs or labour are outside PROVISIONAL expected range — additional human review."
            )
        elif ctx.financial.financial_status in (
            FinancialStatus.NEEDS_REVIEW,
            FinancialStatus.INSUFFICIENT_DATA,
        ):
            triggered.append("R_FINANCIAL_REVIEW")
            reasons.append(f"Financial validation status: {ctx.financial.financial_status.value}.")

    if "R_FINANCIAL_DISCREPANCY" in triggered and tv.technical_status == TechnicalStatus.SUPPORTED:
        return OverallRecommendation.FLAG_FOR_REVIEW, reasons, triggered

    overall = map_overall_recommendation(ctx, triggered=triggered)

    if (
        tv.technical_status == TechnicalStatus.SUPPORTED
        and not tv.human_review_required
        and overall == OverallRecommendation.FLAG_FOR_REVIEW
        and "R_LLM_DISAGREEMENT" not in triggered
        and "R_CONTRADICTIONS" not in triggered
    ):
        triggered.append("R_TECHNICAL_SUPPORT")
        reasons.append("Technical validation supports repair; proceed to human review.")
        return OverallRecommendation.PROCEED_TO_HUMAN_REVIEW, reasons, triggered

    if overall == OverallRecommendation.FLAG_FOR_REVIEW and "R_DEFAULT_REVIEW" not in triggered:
        triggered.append("R_DEFAULT_REVIEW")
        reasons.append("Claim requires human review before any decision.")

    return overall, reasons, triggered

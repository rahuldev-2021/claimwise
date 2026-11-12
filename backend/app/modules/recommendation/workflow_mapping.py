"""Map Phase 4 + LLM advisory signals to workflow recommendation enums."""

from app.modules.llm.schemas.llm_assessment import WorkflowRecommendationType
from app.modules.recommendation.schemas.context import RecommendationContext
from app.schemas.recommendation import OverallRecommendation
from app.schemas.technical_validation import RepairJustificationStatus, TechnicalStatus


def map_workflow_type(ctx: RecommendationContext) -> WorkflowRecommendationType | None:
    if ctx.llm_assessment and ctx.llm_assessment.assessment.workflow_recommendation:
        return ctx.llm_assessment.assessment.workflow_recommendation.type
    return None


def map_overall_recommendation(
    ctx: RecommendationContext,
    *,
    triggered: list[str],
) -> OverallRecommendation:
    tv = ctx.technical

    if "R_INCOMPLETE_ASSESSMENT" in triggered and not tv.supporting_evidence:
        return OverallRecommendation.INSUFFICIENT_INFORMATION

    if "R_INSUFFICIENT_EVIDENCE" in triggered:
        return OverallRecommendation.REQUEST_ADDITIONAL_EVIDENCE

    if "R_CONTRADICTIONS" in triggered:
        return OverallRecommendation.REVIEW_CONTRADICTIONS

    if "R_LLM_DISAGREEMENT" in triggered:
        return OverallRecommendation.FLAG_FOR_REVIEW

    unjustified_ops = [
        a
        for a in tv.repair_action_assessments
        if a.justification_status
        in (
            RepairJustificationStatus.NOT_SUFFICIENTLY_JUSTIFIED,
            RepairJustificationStatus.INSUFFICIENT_INFORMATION,
            RepairJustificationStatus.PARTIALLY_JUSTIFIED,
        )
    ]
    if unjustified_ops:
        return OverallRecommendation.REVIEW_REPAIR_SCOPE

    advisory = map_workflow_type(ctx)
    if advisory == WorkflowRecommendationType.REQUEST_FURTHER_DIAGNOSIS:
        return OverallRecommendation.REQUEST_FURTHER_DIAGNOSIS
    if advisory == WorkflowRecommendationType.REQUEST_ADDITIONAL_EVIDENCE:
        return OverallRecommendation.REQUEST_ADDITIONAL_EVIDENCE

    if tv.technical_status == TechnicalStatus.SUPPORTED and not tv.human_review_required:
        return OverallRecommendation.PROCEED_TO_HUMAN_REVIEW

    return OverallRecommendation.FLAG_FOR_REVIEW

"""Python business-rules recommendation engine."""

from app.modules.recommendation.business_rules import apply_business_rules
from app.modules.recommendation.explanation_builder import build_explanation
from app.modules.recommendation.schemas.context import RecommendationContext
from app.schemas.recommendation import ClaimRecommendation, FinancialAssessmentStatus


class RecommendationEngine:
    def recommend(self, ctx: RecommendationContext) -> ClaimRecommendation:
        overall, reasons, triggered = apply_business_rules(ctx)
        explanation_lines = build_explanation(overall, ctx)
        evidence_ids = list(
            dict.fromkeys(
                e.document_id
                for e in ctx.technical.supporting_evidence + ctx.technical.contradictory_evidence
            )
        )
        missing = list(
            dict.fromkeys(ctx.technical.missing_evidence + [m.message for m in ctx.nlp.missing_information])
        )
        llm_summary = None
        llm_structured = None
        workflow = None
        if ctx.llm_assessment and ctx.llm_available:
            llm_structured = ctx.llm_assessment.assessment
            llm_summary = ctx.llm_assessment.assessment.summary
            workflow = ctx.llm_assessment.assessment.workflow_recommendation

        if not ctx.financial_enabled:
            fin_status = FinancialAssessmentStatus.PENDING
        elif ctx.financial and ctx.financial.predicted_parts_cost is not None:
            fin_status = FinancialAssessmentStatus.AVAILABLE
        elif ctx.financial:
            fin_status = FinancialAssessmentStatus.UNAVAILABLE
        else:
            fin_status = FinancialAssessmentStatus.UNAVAILABLE

        return ClaimRecommendation(
            claim_id=ctx.claim.claim_id,
            technical_validation=ctx.technical,
            financial_validation=ctx.financial,
            overall_recommendation=overall,
            recommendation_reasons=explanation_lines,
            evidence_document_ids=evidence_ids,
            missing_information=missing,
            human_review_required=True,
            triggered_business_rules=triggered,
            financial_assessment_status=fin_status,
            llm_advisory_summary=llm_summary,
            workflow_recommendation=workflow,
            llm_structured=llm_structured,
            repair_action_assessments=list(ctx.technical.repair_action_assessments),
        )

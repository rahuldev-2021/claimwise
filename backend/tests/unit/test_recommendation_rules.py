from datetime import datetime, timezone
from decimal import Decimal

from app.modules.llm.schemas.llm_assessment import LLMAssessmentResponse, LLMContextualAssessment, TechnicalAlignment
from app.modules.nlp.schemas import (
    ComplaintDiagnosisComparison,
    MissingInfoSeverity,
    MissingInformationItem,
    NLPAnalysisResult,
    ProcessingMetadata,
    RecommendedRepairExtraction,
    StructuredExtraction,
)
from app.modules.recommendation.business_rules import apply_business_rules
from app.modules.recommendation.recommendation_engine import RecommendationEngine
from app.modules.recommendation.schemas.context import RecommendationContext
from app.schemas.claim import ClaimInput, ClaimStatus
from app.schemas.llm_execution import LLMExecutionRecord, LLMExecutionStatus
from app.schemas.financial_validation import FinancialStatus, FinancialValidationResult
from app.schemas.recommendation import OverallRecommendation
from app.schemas.repair import Repair
from app.schemas.technical_validation import TechnicalStatus, TechnicalValidationResult
from app.schemas.vehicle import Vehicle


def _claim() -> ClaimInput:
    return ClaimInput(
        claim_id="CLM-T",
        submission_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        vehicle=Vehicle(
            vehicle_id="VH-1",
            make="Ford",
            model="F-150",
            model_year=2023,
            engine_type="3.5L",
            mileage=1000,
        ),
        customer_complaint="brake noise",
        technician_diagnosis="worn pads",
        recommended_repair=Repair(
            repair_category="BRAKING",
            part_number="X",
            part_description="pads",
            recommended_action="replace pads",
        ),
        submitted_parts_cost=Decimal("100"),
        submitted_labour_hours=Decimal("1"),
        claim_status=ClaimStatus.SUBMITTED,
    )


def _nlp(claim: ClaimInput) -> NLPAnalysisResult:
    return NLPAnalysisResult(
        claim_id=claim.claim_id,
        original_complaint=claim.customer_complaint,
        original_diagnosis=claim.technician_diagnosis,
        normalized_complaint=claim.customer_complaint,
        normalized_diagnosis=claim.technician_diagnosis,
        recommended_repair=RecommendedRepairExtraction(
            repair_category="BRAKING",
            part_description="pads",
            recommended_action="replace",
        ),
        complaint_diagnosis_comparison=ComplaintDiagnosisComparison(),
        structured_extraction=StructuredExtraction(),
        processing_metadata=ProcessingMetadata(),
    )


def test_nlp_info_missing_does_not_trigger_insufficient_evidence_rule():
    claim = _claim()
    nlp = _nlp(claim)
    nlp.missing_information = [
        MissingInformationItem(
            code="SYMPTOM_ONSET_MILEAGE_IN_NARRATIVE",
            message="Mileage in narrative only.",
            severity=MissingInfoSeverity.INFO,
        )
    ]
    tv = TechnicalValidationResult(
        claim_id=claim.claim_id,
        technical_status=TechnicalStatus.SUPPORTED,
        diagnosis_summary="ok",
        repair_assessment="ok",
        human_review_required=False,
    )
    ctx = RecommendationContext(
        claim=claim,
        nlp=nlp,
        technical=tv,
        llm_assessment=None,
        llm_execution=LLMExecutionRecord(status=LLMExecutionStatus.DISABLED),
        retrieval_passage_count=2,
    )
    _, _, triggered = apply_business_rules(ctx)
    assert "R_INSUFFICIENT_EVIDENCE" not in triggered


def test_insufficient_evidence_requests_more():
    claim = _claim()
    tv = TechnicalValidationResult(
        claim_id=claim.claim_id,
        technical_status=TechnicalStatus.INSUFFICIENT_EVIDENCE,
        diagnosis_summary="x",
        repair_assessment="y",
        missing_evidence=["No pad thickness"],
    )
    ctx = RecommendationContext(
        claim=claim,
        nlp=_nlp(claim),
        technical=tv,
        llm_assessment=None,
        llm_execution=LLMExecutionRecord(status=LLMExecutionStatus.DISABLED),
        retrieval_passage_count=1,
    )
    rec = RecommendationEngine().recommend(ctx)
    assert rec.overall_recommendation == OverallRecommendation.REQUEST_MORE_EVIDENCE
    assert rec.human_review_required is True


def test_llm_disagreement_does_not_change_technical_validation():
    claim = _claim()
    tv = TechnicalValidationResult(
        claim_id=claim.claim_id,
        technical_status=TechnicalStatus.SUPPORTED,
        diagnosis_summary="ok",
        repair_assessment="ok",
        human_review_required=False,
    )
    llm = LLMContextualAssessment(
        assessment=LLMAssessmentResponse(
            summary="misaligned",
            suggested_alignment=TechnicalAlignment.MISALIGNED,
        )
    )
    ctx = RecommendationContext(
        claim=claim,
        nlp=_nlp(claim),
        technical=tv,
        llm_assessment=llm,
        llm_execution=LLMExecutionRecord(status=LLMExecutionStatus.SUCCESS),
        retrieval_passage_count=2,
    )
    rec = RecommendationEngine().recommend(ctx)
    assert rec.technical_validation is not None
    assert rec.technical_validation.technical_status == TechnicalStatus.SUPPORTED
    assert rec.overall_recommendation == OverallRecommendation.FLAG_FOR_REVIEW
    assert "R_LLM_DISAGREEMENT" in rec.triggered_business_rules


def test_financial_discrepancy_flags_review_not_auto_reject():
    claim = _claim()
    tv = TechnicalValidationResult(
        claim_id=claim.claim_id,
        technical_status=TechnicalStatus.SUPPORTED,
        diagnosis_summary="ok",
        repair_assessment="ok",
        human_review_required=False,
    )
    fin = FinancialValidationResult(
        claim_id=claim.claim_id,
        submitted_parts_cost=claim.submitted_parts_cost,
        submitted_labour_hours=claim.submitted_labour_hours,
        predicted_parts_cost=Decimal("50"),
        predicted_labour_hours=Decimal("1"),
        financial_status=FinancialStatus.OUTSIDE_EXPECTED_RANGE,
        explanation="provisional band",
    )
    ctx = RecommendationContext(
        claim=claim,
        nlp=_nlp(claim),
        technical=tv,
        llm_assessment=None,
        llm_execution=LLMExecutionRecord(status=LLMExecutionStatus.DISABLED),
        financial=fin,
        financial_available=True,
        financial_enabled=True,
        retrieval_passage_count=2,
    )
    rec = RecommendationEngine().recommend(ctx)
    assert rec.overall_recommendation == OverallRecommendation.FLAG_FOR_REVIEW
    assert "R_FINANCIAL_DISCREPANCY" in rec.triggered_business_rules
    assert rec.overall_recommendation != OverallRecommendation.PROCEED_TO_HUMAN_REVIEW

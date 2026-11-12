"""Unit tests for the technical validation rule engine."""

from datetime import datetime, timezone
from decimal import Decimal

from app.modules.nlp.schemas import (
    ComplaintDiagnosisComparison,
    NLPAnalysisResult,
    ProcessingMetadata,
    RecommendedRepairExtraction,
    StructuredExtraction,
)
from app.modules.rag.schemas import RetrievalResult, RetrievalStrategy, RetrievedPassage


def _empty_retrieval() -> RetrievalResult:
    return RetrievalResult(query="", strategy=RetrievalStrategy.HYBRID)
from app.modules.technical_validation.complaint_diagnosis_validator import assess_complaint_diagnosis
from app.modules.technical_validation.schemas import (
    ClassifiedEvidence,
    ComplaintDiagnosisAssessment,
    ValidationContext,
)
from app.modules.technical_validation.validation_rules import apply_rules
from app.schemas.claim import ClaimInput, ClaimStatus
from app.schemas.repair import Repair
from app.schemas.technical_validation import (
    ConsistencyLevel,
    EvidenceSupportClass,
    TechnicalStatus,
)
from app.schemas.vehicle import Vehicle


def _claim(
    claim_id: str = "CLM-T",
    complaint: str = "Brake squeal",
    diagnosis: str = "Worn brake pads",
    repair_action: str = "Replace front brake pads",
) -> ClaimInput:
    return ClaimInput(
        claim_id=claim_id,
        submission_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        vehicle=Vehicle(
            vehicle_id="VH-1",
            make="Ford",
            model="F-150",
            model_year=2023,
            engine_type="3.5L",
            mileage=10000,
        ),
        customer_complaint=complaint,
        technician_diagnosis=diagnosis,
        recommended_repair=Repair(
            repair_category="BRAKING",
            part_number="X",
            part_description="Brake pad set",
            recommended_action=repair_action,
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
            repair_category=claim.recommended_repair.repair_category,
            part_number=claim.recommended_repair.part_number,
            part_description=claim.recommended_repair.part_description,
            recommended_action=claim.recommended_repair.recommended_action,
        ),
        complaint_diagnosis_comparison=ComplaintDiagnosisComparison(),
        structured_extraction=StructuredExtraction(component="brake pad"),
        processing_metadata=ProcessingMetadata(),
    )


def test_empty_retrieval_triggers_r_empty():
    claim = _claim(diagnosis="Suspect pad wear only")
    nlp = _nlp(claim)
    ctx = ValidationContext(
        claim=claim,
        nlp=nlp,
        retrieval=_empty_retrieval(),
        empty_retrieval=True,
        complaint_diagnosis=assess_complaint_diagnosis(claim, nlp),
    )
    ctx = apply_rules(ctx)
    assert "R_EMPTY_RETRIEVAL" in ctx.triggered_rules
    assert ctx.suggested_status in (
        TechnicalStatus.INSUFFICIENT_EVIDENCE,
        TechnicalStatus.NEEDS_REVIEW,
    )
    assert ctx.human_review_required is True


def test_suspected_no_findings_without_direct_evidence():
    claim = _claim(diagnosis="Suspect timing chain wear")
    nlp = _nlp(claim)
    ctx = ValidationContext(
        claim=claim,
        nlp=nlp,
        retrieval=_empty_retrieval(),
        complaint_diagnosis=assess_complaint_diagnosis(claim, nlp),
        classified=[
            ClassifiedEvidence(
                document_id="DOC-009",
                chunk_id="c1",
                title="History",
                document_type="REPAIR_HISTORY",
                verification_status="VERIFIED",
                excerpt="Prior repair",
                support_class=EvidenceSupportClass.INDIRECT_SUPPORT,
                retrieval_score=0.9,
                quality_score=0.4,
            )
        ],
        history_only=True,
    )
    ctx = apply_rules(ctx)
    assert "R_SUSPECTED_NO_FINDINGS" in ctx.triggered_rules
    assert ctx.suggested_status != TechnicalStatus.SUPPORTED


def test_direct_verified_can_support_when_unblocked():
    claim = _claim()
    nlp = _nlp(claim)
    from app.modules.technical_validation.schemas import RepairJustificationAssessment

    ctx = ValidationContext(
        claim=claim,
        nlp=nlp,
        retrieval=_empty_retrieval(),
        complaint_diagnosis=ComplaintDiagnosisAssessment(
            consistency=ConsistencyLevel.CONSISTENT,
            summary="Aligned",
        ),
        repair_justification=RepairJustificationAssessment(
            summary="Aligned repair",
            heavy_vs_light_mismatch=False,
        ),
        classified=[
            ClassifiedEvidence(
                document_id="DOC-002",
                chunk_id="c1",
                title="Pad inspection",
                document_type="TECHNICIAN_REPORT",
                verification_status="VERIFIED",
                excerpt="Pad thickness measured 1.5mm",
                support_class=EvidenceSupportClass.DIRECT_SUPPORT,
                retrieval_score=0.85,
                quality_score=0.8,
            )
        ],
    )
    ctx = apply_rules(ctx)
    assert "R_DIRECT_VERIFIED_SUPPORT" in ctx.triggered_rules
    assert ctx.suggested_status == TechnicalStatus.SUPPORTED
    assert ctx.human_review_required is False


def test_high_retrieval_score_contextual_does_not_imply_supported():
    """Scenario N: semantic rank alone must not yield SUPPORTED."""
    claim = _claim()
    nlp = _nlp(claim)
    ctx = ValidationContext(
        claim=claim,
        nlp=nlp,
        retrieval=RetrievalResult(
            query="brake",
            strategy=RetrievalStrategy.SEMANTIC,
            passages=[
                RetrievedPassage(
                    chunk_id="c1",
                    document_id="DOC-011",
                    title="Part catalog",
                    document_type="PART_REFERENCE",
                    verification_status="VERIFIED",
                    text="Brake pad part listing.",
                    retrieval_method=RetrievalStrategy.SEMANTIC,
                    score=0.99,
                    rank=1,
                )
            ],
        ),
        complaint_diagnosis=ComplaintDiagnosisAssessment(
            consistency=ConsistencyLevel.PARTIALLY_CONSISTENT,
            summary="Partial",
        ),
        classified=[
            ClassifiedEvidence(
                document_id="DOC-011",
                chunk_id="c1",
                title="Part catalog",
                document_type="PART_REFERENCE",
                verification_status="VERIFIED",
                excerpt="Brake pad part listing.",
                support_class=EvidenceSupportClass.CONTEXTUAL,
                retrieval_score=0.99,
                quality_score=0.35,
            )
        ],
        history_only=True,
    )
    ctx = apply_rules(ctx)
    assert ctx.suggested_status != TechnicalStatus.SUPPORTED

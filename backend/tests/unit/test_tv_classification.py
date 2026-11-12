"""Unit tests for passage classification and quality vs retrieval score."""

from datetime import datetime, timezone
from decimal import Decimal

from app.modules.rag.schemas import RetrievalResult, RetrievalStrategy, RetrievedPassage
from app.modules.technical_validation.diagnostic_evidence_validator import classify_retrieval
from app.schemas.claim import ClaimInput, ClaimStatus
from app.schemas.repair import Repair
from app.schemas.technical_validation import EvidenceSupportClass
from app.schemas.vehicle import Vehicle


def _claim() -> ClaimInput:
    return ClaimInput(
        claim_id="CLM-002",
        submission_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        vehicle=Vehicle(
            vehicle_id="VH-1002",
            make="Ford",
            model="F-150",
            model_year=2023,
            engine_type="3.5L",
            mileage=32000,
        ),
        customer_complaint="Squealing when braking",
        technician_diagnosis="Front brake pads worn below minimum thickness.",
        recommended_repair=Repair(
            repair_category="BRAKING",
            part_number="HL3Z-2001-D",
            part_description="Front brake pad set",
            recommended_action="Replace front brake pads",
        ),
        submitted_parts_cost=Decimal("320"),
        submitted_labour_hours=Decimal("2.5"),
        claim_status=ClaimStatus.UNDER_REVIEW,
    )


def test_repair_history_capped_indirect():
    claim = _claim()
    retrieval = RetrievalResult(
        query="history",
        strategy=RetrievalStrategy.HYBRID,
        passages=[
            RetrievedPassage(
                chunk_id="h1",
                document_id="DOC-009",
                title="Prior timing chain",
                document_type="REPAIR_HISTORY",
                verification_status="VERIFIED",
                text="Timing chain replaced previously.",
                retrieval_method=RetrievalStrategy.HYBRID,
                score=0.92,
                rank=1,
            )
        ],
    )
    classified = classify_retrieval(claim, retrieval)
    assert classified[0].support_class == EvidenceSupportClass.INDIRECT_SUPPORT


def test_retrieval_score_not_equal_quality_score():
    claim = _claim()
    retrieval = RetrievalResult(
        query="history",
        strategy=RetrievalStrategy.HYBRID,
        passages=[
            RetrievedPassage(
                chunk_id="c1",
                document_id="DOC-002",
                title="Pad measurement",
                document_type="TECHNICIAN_REPORT",
                verification_status="VERIFIED",
                text="Pad thickness measured at 1.8 mm, below minimum specification 2.0mm.",
                retrieval_method=RetrievalStrategy.HYBRID,
                score=0.77,
                rank=1,
                metadata={"vehicle_make": "Ford", "vehicle_model": "F-150", "model_year": 2023},
            )
        ],
    )
    item = classify_retrieval(claim, retrieval)[0]
    assert item.support_class == EvidenceSupportClass.DIRECT_SUPPORT
    assert item.retrieval_score != item.quality_score

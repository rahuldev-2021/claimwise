from datetime import datetime, timezone
from decimal import Decimal

from app.modules.technical_validation.technical_validation_pipeline import validate_technical
from app.modules.technical_validation.claim_submission_evidence import CLAIM_SUBMISSION_DOC_ID
from app.modules.nlp.schemas import (
    ComplaintDiagnosisComparison,
    NLPAnalysisResult,
    ProcessingMetadata,
    RecommendedRepairExtraction,
    StructuredExtraction,
)
from app.modules.rag.schemas import RetrievalResult, RetrievalStrategy
from app.schemas.claim import ClaimInput, ClaimStatus
from app.schemas.repair import Repair
from app.schemas.technical_validation import TechnicalStatus
from app.schemas.vehicle import Vehicle


def _nlp(claim_id: str) -> NLPAnalysisResult:
    return NLPAnalysisResult(
        claim_id=claim_id,
        original_complaint="noise",
        original_diagnosis="pads",
        normalized_complaint="noise",
        normalized_diagnosis="pads",
        recommended_repair=RecommendedRepairExtraction(
            repair_category="BRAKING",
            part_description="pads",
            recommended_action="replace",
        ),
        complaint_diagnosis_comparison=ComplaintDiagnosisComparison(
            matching_components=["brake", "front brake pad"],
        ),
        structured_extraction=StructuredExtraction(symptom="squeal", component="brake"),
        processing_metadata=ProcessingMetadata(),
    )


def test_supported_dealer_measurements_yield_supported_not_history_only():
    claim = ClaimInput(
        claim_id="CLM-EVAL-SUPPORTED",
        submission_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
        vehicle=Vehicle(
            vehicle_id="V1",
            make="Ford",
            model="F-150",
            model_year=2023,
            mileage=28500,
            engine_type="3.5L EcoBoost",
        ),
        customer_complaint="Squealing when braking at low speed near 28,000 miles.",
        technician_diagnosis=(
            "Measured front brake pad thickness: inner 1.2 mm (minimum spec 2.0 mm), "
            "outer 3.1 mm. Rotors show minor scoring within resurfacing tolerance."
        ),
        recommended_repair=Repair(
            repair_category="BRAKING",
            part_description="front brake pads",
            recommended_action="Replace front brake pads and resurface rotors.",
        ),
        submitted_parts_cost=Decimal("425"),
        submitted_labour_hours=Decimal("3.25"),
        claim_status=ClaimStatus.SUBMITTED,
    )
    retrieval = RetrievalResult(
        query="brake",
        strategy=RetrievalStrategy.HYBRID,
        passages=[],
    )
    result = validate_technical(claim, _nlp(claim.claim_id), retrieval)
    assert result.technical_status == TechnicalStatus.SUPPORTED
    assert "R_HISTORY_ONLY" not in result.triggered_rules
    assert "R_CLAIM_ATTESTED_INSPECTION" in result.triggered_rules or "R_DIRECT_VERIFIED_SUPPORT" in result.triggered_rules
    assert any(e.document_id == CLAIM_SUBMISSION_DOC_ID for e in result.supporting_evidence)

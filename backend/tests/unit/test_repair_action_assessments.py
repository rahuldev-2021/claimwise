from datetime import datetime, timezone
from decimal import Decimal

from app.modules.nlp.schemas import (
    ComplaintDiagnosisComparison,
    NLPAnalysisResult,
    ProcessingMetadata,
    RecommendedRepairExtraction,
    StructuredExtraction,
)
from app.modules.technical_validation.repair_justification_validator import assess_repair_actions
from app.schemas.claim import ClaimInput, ClaimStatus
from app.schemas.repair import Repair
from app.schemas.technical_validation import RepairJustificationStatus
from app.schemas.vehicle import Vehicle


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
        structured_extraction=StructuredExtraction(component="brake_pad"),
        processing_metadata=ProcessingMetadata(),
    )


def test_brake_pads_and_rotors_split():
    claim = ClaimInput(
        claim_id="CLM-BR",
        submission_date=datetime.now(timezone.utc),
        vehicle=Vehicle(vehicle_id="V", make="Ford", model="F-150", model_year=2020),
        customer_complaint="Squeal when braking",
        technician_diagnosis="Front brake pads worn below minimum. Rotors show heat spots.",
        recommended_repair=Repair(
            repair_category="BRAKING",
            part_description="pads",
            recommended_action="Replace front brake pads and resurface front rotors",
        ),
        submitted_parts_cost=Decimal("0"),
        submitted_labour_hours=Decimal("1"),
        claim_status=ClaimStatus.SUBMITTED,
    )
    actions = assess_repair_actions(claim, _nlp(claim), [])
    assert len(actions) == 2
    pad = next(a for a in actions if "pad" in a.normalized_operation)
    rotor = next(a for a in actions if "rotor" in a.normalized_operation)
    assert pad.justification_status == RepairJustificationStatus.JUSTIFIED
    assert rotor.justification_status in (
        RepairJustificationStatus.PARTIALLY_JUSTIFIED,
        RepairJustificationStatus.JUSTIFIED,
    )
    assert pad.associated_diagnostic_findings
    assert "heat" in rotor.explanation.lower() or "rotor" in rotor.explanation.lower()

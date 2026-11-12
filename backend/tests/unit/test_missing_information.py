from datetime import datetime, timezone
from decimal import Decimal

from app.modules.nlp.information_extractor import extract_from_claim
from app.modules.nlp.missing_information import detect_missing_information
from app.modules.nlp.pipeline import NLPPipeline
from app.repositories.sample_claim_repository import SampleClaimRepository
from tests.conftest import SAMPLE_DATA_DIR


def test_clm001_suggests_heavy_repair_without_documents():
    repo = SampleClaimRepository(SAMPLE_DATA_DIR)
    claim = repo.get_claim("CLM-001")
    extractions, _ = extract_from_claim(claim)
    missing = detect_missing_information(claim, extractions)
    codes = {m.code for m in missing}
    assert "NO_SUPPORTING_DOCUMENTS" not in codes or claim.supporting_document_ids
    pipeline = NLPPipeline()
    result = pipeline.analyze(claim)
    assert any(
        m.code in ("MISSING_DIAGNOSTIC_EVIDENCE", "THIN_DIAGNOSTIC_SUPPORT", "THIN_DIAGNOSIS")
        or "diagnosis" in m.message.lower()
        for m in result.missing_information
    )


def test_empty_diagnosis_suggestion():
    from app.schemas.claim import ClaimInput
    from app.schemas.repair import Repair
    from app.schemas.vehicle import Vehicle

    claim = ClaimInput(
        claim_id="X",
        submission_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        vehicle=Vehicle(vehicle_id="V", make="Ford", model="X", model_year=2020),
        customer_complaint="Noise when braking during stops in traffic.",
        technician_diagnosis="Bad brakes.",
        recommended_repair=Repair(
            repair_category="BRAKING",
            part_description="Pads",
            recommended_action="Replace pads",
        ),
        submitted_parts_cost=Decimal("0"),
        submitted_labour_hours=Decimal("1"),
    )
    extractions, _ = extract_from_claim(claim)
    missing = detect_missing_information(claim, extractions)
    assert any(m.code == "THIN_DIAGNOSIS" for m in missing)

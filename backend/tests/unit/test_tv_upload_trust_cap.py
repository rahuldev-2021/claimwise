from datetime import datetime, timezone

from app.modules.rag.schemas import RetrievedPassage, RetrievalStrategy
from app.modules.technical_validation.evidence.evidence_trust_policy import (
    assess_passage_trust,
    display_quality_score,
)
from app.modules.technical_validation.schemas import EvidenceSupportClass
from app.schemas.claim import ClaimInput, ClaimStatus
from app.schemas.repair import Repair
from app.schemas.vehicle import Vehicle
from datetime import datetime, timezone
from decimal import Decimal


def _minimal_claim() -> ClaimInput:
    return ClaimInput(
        claim_id="CLM-T",
        submission_date=datetime.now(timezone.utc),
        vehicle=Vehicle(vehicle_id="V", make="Ford", model="F-150", model_year=2020),
        customer_complaint="Brake noise",
        technician_diagnosis="Pad wear",
        recommended_repair=Repair(repair_category="BRAKING", part_description="pads", recommended_action="replace"),
        submitted_parts_cost=Decimal("0"),
        submitted_labour_hours=Decimal("1"),
        claim_status=ClaimStatus.SUBMITTED,
    )


def test_claim_upload_pending_caps_quality():
    passage = RetrievedPassage(
        chunk_id="c1",
        document_id="d1",
        title="upload.pdf",
        document_type="TECHNICIAN_REPORT",
        verification_status="PENDING",
        evidence_source_type="CLAIM_UPLOAD",
        evidence_scope="claim",
        text="Some technician narrative without measurements.",
        retrieval_method=RetrievalStrategy.HYBRID,
        score=0.8,
        rank=1,
    )
    dims = assess_passage_trust(
        passage, _minimal_claim(), support_class=EvidenceSupportClass.DIRECT_SUPPORT, vehicle_applicable=True
    )
    quality = display_quality_score(dims)
    assert quality <= 0.55

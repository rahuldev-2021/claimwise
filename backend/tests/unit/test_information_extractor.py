from datetime import datetime, timezone
from decimal import Decimal

from app.modules.nlp.information_extractor import extract_from_claim
from app.modules.nlp.schemas import TextSourceField
from app.schemas.claim import ClaimInput
from app.schemas.repair import Repair
from app.schemas.vehicle import Vehicle


def _minimal_claim(**overrides) -> ClaimInput:
    base = dict(
        claim_id="TST-1",
        submission_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        vehicle=Vehicle(vehicle_id="V1", make="Ford", model="Mustang", model_year=2022),
        customer_complaint="Brake squeal and engine knock when accelerating",
        technician_diagnosis="Worn brake pads; possible timing chain noise",
        recommended_repair=Repair(
            repair_category="BRAKING",
            part_description="Brake pads",
            recommended_action="Replace front brake pads",
        ),
        submitted_parts_cost=Decimal("100"),
        submitted_labour_hours=Decimal("2"),
    )
    base.update(overrides)
    return ClaimInput(**base)


def test_multiple_fields_extracted():
    extractions, _ = extract_from_claim(_minimal_claim())
    sources = {e.source_field for e in extractions}
    assert TextSourceField.CUSTOMER_COMPLAINT in sources
    assert TextSourceField.TECHNICIAN_DIAGNOSIS in sources
    assert TextSourceField.RECOMMENDED_REPAIR in sources

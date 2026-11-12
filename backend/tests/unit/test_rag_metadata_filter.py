from datetime import datetime, timezone
from decimal import Decimal

from app.modules.rag.metadata_filter import build_from_claim, build_where
from app.schemas.claim import ClaimInput
from app.schemas.repair import Repair
from app.schemas.vehicle import Vehicle


def _claim() -> ClaimInput:
    return ClaimInput(
        claim_id="MF-1",
        submission_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        vehicle=Vehicle(vehicle_id="V1", make="Ford", model="F-150", model_year=2023),
        customer_complaint="brake noise",
        technician_diagnosis="pad wear",
        recommended_repair=Repair(
            repair_category="BRAKING",
            part_description="Brake pads",
            recommended_action="Replace",
        ),
        submitted_parts_cost=Decimal("0"),
        submitted_labour_hours=Decimal("1"),
    )


def test_build_where_in_operator():
    clause = build_where({"repair_category": ["BRAKING", "ENGINE"]})
    assert clause == {"repair_category": {"$in": ["BRAKING", "ENGINE"]}}


def test_build_from_claim_only_present_fields():
    where = build_from_claim(_claim(), fields=("repair_category", "vehicle_make"))
    assert where == {
        "$and": [
            {"repair_category": "BRAKING"},
            {"vehicle_make": "Ford"},
        ]
    }

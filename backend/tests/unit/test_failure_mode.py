from datetime import datetime, timezone
from decimal import Decimal

from app.modules.nlp.pipeline import NLPPipeline
from app.schemas.claim import ClaimInput
from app.schemas.repair import Repair
from app.schemas.vehicle import Vehicle


def _claim(complaint: str, diagnosis: str) -> ClaimInput:
    return ClaimInput(
        claim_id="FM-TST",
        submission_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        vehicle=Vehicle(vehicle_id="V1", make="Ford", model="Focus", model_year=2020),
        customer_complaint=complaint,
        technician_diagnosis=diagnosis,
        recommended_repair=Repair(
            repair_category="ENGINE",
            part_description="Inspect",
            recommended_action="Inspect",
        ),
        submitted_parts_cost=Decimal("0"),
        submitted_labour_hours=Decimal("1"),
    )


def test_symptom_does_not_become_failure_mode():
    result = NLPPipeline().analyze(
        _claim(
            "engine makes abnormal noise",
            "possible timing chain noise on inspection",
        )
    )
    assert result.structured_extraction.symptom == "abnormal_noise"
    assert result.structured_extraction.failure_mode is None


def test_explicit_failure_mode_from_diagnosis():
    result = NLPPipeline().analyze(
        _claim(
            "coolant smell in cabin",
            "technician confirms coolant leakage from the radiator",
        )
    )
    assert result.structured_extraction.failure_mode == "leakage"

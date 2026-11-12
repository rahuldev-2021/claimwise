from datetime import datetime, timezone

from app.modules.financial_validation.config.loader import load_financial_config
from app.modules.financial_validation.features.feature_engineering import extract_inference_features
from app.schemas.claim import ClaimInput, ClaimStatus
from app.schemas.repair import Repair
from app.schemas.vehicle import Vehicle


def _sample_claim(**kwargs) -> ClaimInput:
    return ClaimInput(
        claim_id="CLM-TST-1",
        submission_date=datetime(2024, 6, 1, tzinfo=timezone.utc),
        vehicle=Vehicle(
            vehicle_id="V1",
            make="ACME",
            model="Sedan",
            model_year=2019,
            mileage=40000,
            engine_type="V6",
        ),
        customer_complaint="Engine noise",
        technician_diagnosis="Timing chain wear",
        recommended_repair=Repair(
            repair_category="ENGINE",
            part_number="PN-1",
            part_description="Chain kit",
            recommended_action="Replace timing chain",
        ),
        submitted_parts_cost="1200",
        submitted_labour_hours="8",
        currency="USD",
        claim_status=ClaimStatus.SUBMITTED,
        **kwargs,
    )


def test_extract_inference_features_includes_vehicle_age():
    mapping = load_financial_config("config/financial").feature_mapping
    result = extract_inference_features(_sample_claim(), mapping)
    assert "vehicle_age" in result.features
    assert result.features["vehicle_age"] == 5
    assert result.features["part_description"] == "Chain kit"
    assert result.features["repair_action"].startswith("Replace")
    assert not result.missing_critical


def test_vehicle_category_lookup_fallback():
    mapping = load_financial_config("config/financial").feature_mapping
    claim = _sample_claim()
    result = extract_inference_features(claim, mapping)
    assert result.features.get("vehicle_category") == "SEDAN"


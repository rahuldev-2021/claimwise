from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.core.config import Settings
from app.modules.financial_validation.config.loader import load_financial_config
from app.modules.financial_validation.features.feature_engineering import extract_inference_features
from app.modules.financial_validation.models.model_registry import ModelRegistry
from app.modules.financial_validation.services.financial_validation_service import FinancialValidationService
from app.modules.financial_validation.services.prediction_service import (
    PredictionService,
    resolve_registry_for_settings,
)
from app.schemas.claim import ClaimInput, ClaimStatus
from app.schemas.repair import Repair
from app.schemas.vehicle import Vehicle

pytestmark = pytest.mark.financial_ml

EXP_ROOT = Path("data/financial_models/synthetic_v1/experimental_artifacts")


@pytest.fixture()
def sample_claim() -> ClaimInput:
    return ClaimInput(
        claim_id="CLM-G3-1",
        submission_date=datetime(2024, 6, 1, tzinfo=timezone.utc),
        vehicle=Vehicle(
            vehicle_id="V1",
            make="Bravo",
            model="Executive",
            model_year=2014,
            mileage=66117,
            engine_type="I4-T",
            vehicle_category="SEDAN",
        ),
        customer_complaint="Brakes noise",
        technician_diagnosis="Pad wear",
        recommended_repair=Repair(
            repair_category="BRAKES",
            part_description="Brake pads",
            recommended_action="Replacement",
        ),
        submitted_parts_cost="450",
        submitted_labour_hours="3",
        currency="USD",
        claim_status=ClaimStatus.SUBMITTED,
    )


def test_production_registry_blocks_experimental_entries():
    registry = ModelRegistry(EXP_ROOT)
    for e in registry.load():
        assert not e.eligible_for_inference()
        if e.lifecycle == "experimental":
            assert e.eligible_for_experimental_inference()


def test_experimental_disabled_uses_production_path():
    root, mode, enabled = resolve_registry_for_settings(
        Settings(FINANCIAL_EXPERIMENTAL_MODELS_ENABLED=False)
    )
    assert mode == "production"
    assert enabled is False
    assert root == Path("data/financial_models")


@pytest.mark.skipif(not EXP_ROOT.is_dir(), reason="Gate 2 experimental artifacts missing")
def test_experimental_enabled_loads_predictions(sample_claim):
    bundle = load_financial_config("config/financial")
    settings = Settings(
        FINANCIAL_EXPERIMENTAL_MODELS_ENABLED=True,
        FINANCIAL_EXPERIMENTAL_REGISTRY_DIR=str(EXP_ROOT),
    )
    extraction = extract_inference_features(sample_claim, bundle.feature_mapping)
    out = PredictionService(bundle, settings).predict(extraction)
    assert out.experimental_enabled
    assert out.models_available
    assert out.parts.value is not None
    assert out.labour.value is not None
    assert out.parts.algorithm == "hist_gradient_boosting"
    assert out.limitations


@pytest.mark.skipif(not EXP_ROOT.is_dir(), reason="Gate 2 experimental artifacts missing")
def test_financial_validate_with_experimental(sample_claim):
    settings = Settings(
        FINANCIAL_EXPERIMENTAL_MODELS_ENABLED=True,
        FINANCIAL_EXPERIMENTAL_REGISTRY_DIR=str(EXP_ROOT),
    )
    result = FinancialValidationService(settings).validate(sample_claim)
    assert result.experimental_prediction
    assert result.synthetic_data_prediction
    assert result.human_review_required
    assert result.predicted_parts_cost is not None
    assert result.parts_model_algorithm == "hist_gradient_boosting"


def test_production_mode_no_fake_predictions(sample_claim):
    settings = Settings(
        FINANCIAL_EXPERIMENTAL_MODELS_ENABLED=False,
        FINANCIAL_MODEL_REGISTRY_DIR="data/financial_models",
    )
    result = FinancialValidationService(settings).validate(sample_claim)
    assert result.predicted_parts_cost is None
    assert result.experimental_prediction is False

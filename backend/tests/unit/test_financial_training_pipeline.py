import pytest

pytestmark = pytest.mark.financial_ml

sklearn = pytest.importorskip("sklearn")
pandas = pytest.importorskip("pandas")

from pathlib import Path

from app.core.config import Settings
from app.modules.financial_validation.services.financial_validation_service import (
    FinancialValidationService,
)
from app.modules.financial_validation.training.train_common import train_regressor
from app.services.claim_service import ClaimService


@pytest.fixture()
def synthetic_registry(tmp_path):
    data = Path("tests/fixtures/financial/tiny_training.csv")
    registry = tmp_path / "registry"
    train_regressor(
        "parts_cost",
        data_path=data,
        registry_dir=registry,
        config_dir=Path("config/financial"),
        allow_synthetic_test=True,
        model_candidate="dummy_mean",
    )
    train_regressor(
        "labour_hours",
        data_path=data,
        registry_dir=registry,
        config_dir=Path("config/financial"),
        allow_synthetic_test=True,
        model_candidate="dummy_mean",
    )
    return registry


def test_train_on_synthetic_fixture_only_when_allowed(tmp_path):
    data = Path("tests/fixtures/financial/tiny_training.csv")
    registry = tmp_path / "registry"
    with pytest.raises(Exception):
        train_regressor(
            "parts_cost",
            data_path=data,
            registry_dir=registry,
            config_dir=Path("config/financial"),
            allow_synthetic_test=False,
        )


def test_predict_after_synthetic_train(synthetic_registry, repository):
    settings = Settings(
        FINANCIAL_MODEL_REGISTRY_DIR=str(synthetic_registry),
        FINANCIAL_CONFIG_DIR="config/financial",
    )
    claim = repository.get_claim("CLM-001")
    result = FinancialValidationService(settings).validate(claim)
    assert result.predicted_parts_cost is not None
    assert result.predicted_labour_hours is not None
    assert result.financial_status.value in (
        "WITHIN_EXPECTED_RANGE",
        "OUTSIDE_EXPECTED_RANGE",
        "NEEDS_REVIEW",
    )

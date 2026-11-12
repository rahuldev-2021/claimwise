import pytest

pytestmark = pytest.mark.financial_ml

sklearn = pytest.importorskip("sklearn")

from app.modules.financial_validation.models.regressor_factory import (
    create_regressor,
    resolve_runnable_candidates,
)


@pytest.mark.parametrize(
    "candidate",
    [
        "dummy_mean",
        "linear_regression",
        "ridge",
        "random_forest",
        "gradient_boosting",
        "hist_gradient_boosting",
    ],
)
def test_create_regressor_supported(candidate):
    est = create_regressor(candidate, 42)
    assert hasattr(est, "fit")
    assert hasattr(est, "predict")


def test_xgboost_skipped_when_unavailable():
    runnable, skipped = resolve_runnable_candidates(["ridge", "xgboost"])
    if skipped:
        assert skipped[0]["candidate"] == "xgboost"
        assert skipped[0]["status"] == "NOT RUN"
        assert "ridge" in runnable

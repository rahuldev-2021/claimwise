import numpy as np

from app.modules.financial_validation.training.evaluation import (
    regression_metrics,
    select_best_candidate,
)


def test_regression_metrics_perfect_fit():
    y = np.array([1.0, 2.0, 3.0])
    m = regression_metrics(y, y)
    assert m["mae"] == 0.0
    assert m["rmse"] == 0.0
    assert m["median_absolute_error"] == 0.0
    assert m["r2"] == 1.0


def test_select_best_candidate_by_validation_mae():
    rows = [
        {"candidate": "a", "status": "RUN", "metrics": {"validation": {"mae": 10, "rmse": 5, "r2": 0.5}}},
        {"candidate": "b", "status": "RUN", "metrics": {"validation": {"mae": 2, "rmse": 8, "r2": 0.1}}},
        {"candidate": "xgboost", "status": "NOT RUN", "metrics": {}},
    ]
    best = select_best_candidate(rows, split="validation")
    assert best is not None
    assert best["candidate"] == "b"

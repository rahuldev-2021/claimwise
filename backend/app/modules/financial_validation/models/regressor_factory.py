"""Shared CPU regressor factory for parts cost and labour hours."""

from __future__ import annotations

from typing import Any

from app.modules.financial_validation.exceptions import FinancialDependencyError

# Canonical keys used in configs and comparison orchestration.
STANDARD_CANDIDATE_KEYS: tuple[str, ...] = (
    "dummy_mean",
    "linear_regression",
    "ridge",
    "random_forest",
    "gradient_boosting",
    "hist_gradient_boosting",
    "xgboost",
)


def _normalize_candidate_key(candidate: str) -> str:
    key = candidate.strip().lower().replace("-", "_")
    aliases = {
        "linear": "linear_regression",
        "hist_gradient_boosting_regressor": "hist_gradient_boosting",
        "gradient_boosting_regressor": "gradient_boosting",
        "gbr": "gradient_boosting",
        "rf": "random_forest",
        "xgb": "xgboost",
    }
    return aliases.get(key, key)


def xgboost_available() -> bool:
    try:
        import xgboost  # noqa: F401

        return True
    except ImportError:
        return False


def resolve_runnable_candidates(candidates: list[str]) -> tuple[list[str], list[dict[str, str]]]:
    """Return candidates that can run on this environment and skip records for optional deps."""
    runnable: list[str] = []
    skipped: list[dict[str, str]] = []
    for raw in candidates:
        key = _normalize_candidate_key(raw)
        if key == "xgboost" and not xgboost_available():
            skipped.append(
                {
                    "candidate": raw,
                    "status": "NOT RUN",
                    "reason": "xgboost optional dependency not installed (pip install -e '.[ml-xgb]')",
                }
            )
            continue
        runnable.append(key)
    return runnable, skipped


def create_regressor(candidate: str, random_seed: int = 42) -> Any:
    key = _normalize_candidate_key(candidate)
    from sklearn.dummy import DummyRegressor
    from sklearn.ensemble import (
        GradientBoostingRegressor,
        HistGradientBoostingRegressor,
        RandomForestRegressor,
    )
    from sklearn.linear_model import LinearRegression, Ridge

    if key == "dummy_mean":
        return DummyRegressor(strategy="mean")
    if key == "linear_regression":
        return LinearRegression()
    if key == "ridge":
        return Ridge(random_state=random_seed)
    if key == "random_forest":
        return RandomForestRegressor(
            random_state=random_seed,
            n_estimators=50,
            n_jobs=1,
        )
    if key == "gradient_boosting":
        return GradientBoostingRegressor(random_state=random_seed)
    if key == "hist_gradient_boosting":
        return HistGradientBoostingRegressor(random_state=random_seed)
    if key == "xgboost":
        if not xgboost_available():
            raise FinancialDependencyError(
                "xgboost not installed; install optional extra pip install -e '.[ml-xgb]' or skip candidate"
            )
        from xgboost import XGBRegressor

        return XGBRegressor(
            random_state=random_seed,
            n_estimators=100,
            tree_method="hist",
            n_jobs=1,
        )
    raise ValueError(f"Unknown regressor candidate: {candidate}")

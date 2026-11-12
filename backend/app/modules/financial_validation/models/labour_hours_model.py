"""Labour hours regressor factory."""

from __future__ import annotations

from typing import Any

from app.modules.financial_validation.models.regressor_factory import create_regressor


def create_estimator(candidate: str, random_seed: int = 42) -> Any:
    return create_regressor(candidate, random_seed)

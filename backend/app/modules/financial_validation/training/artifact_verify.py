"""Verify model artifacts before experimental registration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.modules.financial_validation.exceptions import FinancialModelError
from app.modules.financial_validation.models.model_registry import feature_schema_hash


def verify_trained_artifacts(
    *,
    registry_root: Path,
    model_rel: str,
    preprocessor_rel: str,
    feature_ids: list[str],
    feature_cols: list[str],
    sample_feature_row: dict[str, Any],
) -> dict[str, Any]:
    import joblib
    import numpy as np

    from app.modules.financial_validation.data.preprocessing import (
        FinancialFeaturePreprocessor,
        build_feature_frame,
    )

    expected_hash = feature_schema_hash(feature_ids)
    root = registry_root.resolve()
    model_path = (root / model_rel).resolve()
    pre_path = (root / preprocessor_rel).resolve()
    for path in (model_path, pre_path):
        if root not in path.parents and path != root:
            raise FinancialModelError(f"artifact outside registry root: {path}")
        if not path.is_file():
            raise FinancialModelError(f"missing artifact: {path}")

    model = joblib.load(model_path)
    preprocessor = FinancialFeaturePreprocessor.load(pre_path)
    if preprocessor.feature_columns != feature_cols:
        raise FinancialModelError("preprocessor feature column order mismatch")

    frame = build_feature_frame([sample_feature_row], feature_cols)
    transformed = preprocessor.transform(frame)
    pred = model.predict(transformed)
    if not np.all(np.isfinite(pred)):
        raise FinancialModelError("prediction produced non-finite values")

    return {
        "verified": True,
        "feature_schema_hash": expected_hash,
        "model_path": model_rel,
        "preprocessor_path": preprocessor_rel,
        "smoke_prediction": float(pred[0]),
    }

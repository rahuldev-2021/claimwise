"""Sklearn preprocessing fitted on training data only (optional ml extra)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.modules.financial_validation.exceptions import FinancialDependencyError

CATEGORICAL_FEATURES = {
    "vehicle_make",
    "vehicle_model",
    "engine_type",
    "vehicle_category",
    "repair_category",
    "part_description",
    "repair_action",
    "repair_complexity",
    "currency",
}

NUMERIC_FEATURES = {
    "model_year",
    "mileage",
    "vehicle_age",
    "price_year",
}


def _require_ml() -> None:
    try:
        import pandas  # noqa: F401
        import sklearn  # noqa: F401
    except ImportError as exc:
        raise FinancialDependencyError("Install optional ml extra: pip install -e '.[ml]'") from exc


class FinancialFeaturePreprocessor:
    """ColumnTransformer that expects a DataFrame keyed by internal feature ids."""

    def __init__(self, feature_columns: list[str]) -> None:
        _require_ml()
        from sklearn.compose import ColumnTransformer
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import OneHotEncoder
        from sklearn.impute import SimpleImputer

        self.feature_columns = feature_columns
        cat_cols = [c for c in feature_columns if c in CATEGORICAL_FEATURES]
        num_cols = [c for c in feature_columns if c in NUMERIC_FEATURES]

        cat_pipe = Pipeline(
            steps=[
                ("impute", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ]
        )
        num_pipe = Pipeline(
            steps=[("impute", SimpleImputer(strategy="median"))],
        )

        transformers = []
        if cat_cols:
            transformers.append(("cat", cat_pipe, cat_cols))
        if num_cols:
            transformers.append(("num", num_pipe, num_cols))

        self._transformer = ColumnTransformer(transformers=transformers, remainder="drop")

    def fit(self, frame) -> "FinancialFeaturePreprocessor":
        self._transformer.fit(frame[self.feature_columns])
        return self

    def transform(self, frame):
        return self._transformer.transform(frame[self.feature_columns])

    def save(self, path: Path) -> None:
        import joblib

        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"feature_columns": self.feature_columns, "transformer": self._transformer}, path)

    @classmethod
    def load(cls, path: Path) -> "FinancialFeaturePreprocessor":
        import joblib

        payload = joblib.load(path)
        obj = cls(payload["feature_columns"])
        obj._transformer = payload["transformer"]
        return obj


def build_feature_frame(rows: list[dict[str, Any]], feature_columns: list[str]):
    """DataFrame with stable column order for training or inference."""
    _require_ml()
    import pandas as pd

    data = []
    for row in rows:
        data.append({col: row.get(col) for col in feature_columns})
    return pd.DataFrame(data)

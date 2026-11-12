"""ML prediction service — never fabricates values when models are missing."""

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, Optional

from app.core.config import Settings
from app.modules.financial_validation.config.models import FinancialConfigBundle
from app.modules.financial_validation.exceptions import (
    FinancialDependencyError,
    FinancialModelError,
)
from app.modules.financial_validation.models.model_registry import (
    InferenceMode,
    ModelRegistry,
    feature_schema_hash,
)
from app.modules.financial_validation.features.feature_engineering import (
    FeatureExtractionResult,
)

EXPERIMENTAL_LIMITATIONS = "Human review is required."


@dataclass
class TaskPrediction:
    value: Optional[Decimal]
    model_version: Optional[str]
    available: bool
    algorithm: Optional[str] = None
    lifecycle: Optional[str] = None
    synthetic_data: bool = False


@dataclass
class PredictionOutput:
    parts: TaskPrediction
    labour: TaskPrediction
    models_available: bool
    inference_mode: InferenceMode = "production"
    experimental_enabled: bool = False
    limitations: str = ""


def _ml_deps_available() -> bool:
    try:
        import joblib  # noqa: F401
        import sklearn  # noqa: F401

        return True
    except ImportError:
        return False


def resolve_registry_for_settings(
    settings: Settings,
) -> tuple[Path, InferenceMode, bool]:
    """Return registry root and inference mode; experimental requires explicit flag."""
    experimental = bool(settings.FINANCIAL_EXPERIMENTAL_MODELS_ENABLED)
    if experimental:
        return Path(settings.FINANCIAL_EXPERIMENTAL_REGISTRY_DIR), "experimental", True
    return Path(settings.FINANCIAL_MODEL_REGISTRY_DIR), "production", False


def _predict_with_model(
    registry_root: Path,
    entry_rel: str,
    preprocessor_rel: str,
    feature_row: dict[str, Any],
) -> Decimal:
    import joblib

    model_path = (registry_root / entry_rel).resolve()
    pre_path = (registry_root / preprocessor_rel).resolve()
    for path in (model_path, pre_path):
        if (
            registry_root.resolve() not in path.parents
            and path != registry_root.resolve()
        ):
            raise FinancialModelError(
                "Refusing to load artifacts outside trusted registry root"
            )
    from app.modules.financial_validation.data.preprocessing import (
        FinancialFeaturePreprocessor,
        build_feature_frame,
    )

    model = joblib.load(model_path)
    preprocessor = FinancialFeaturePreprocessor.load(pre_path)
    frame = build_feature_frame([feature_row], preprocessor.feature_columns)
    transformed = preprocessor.transform(frame)
    raw = model.predict(transformed)[0]
    return Decimal(str(raw))


class PredictionService:
    def __init__(
        self,
        bundle: FinancialConfigBundle,
        settings: Settings,
    ) -> None:
        self._bundle = bundle
        registry_root, inference_mode, experimental_enabled = (
            resolve_registry_for_settings(settings)
        )
        self._inference_mode = inference_mode
        self._experimental_enabled = experimental_enabled
        self._registry = ModelRegistry(
            registry_root,
            trusted_root_only=bool(
                bundle.training_defaults.registry.get("trusted_root_only", True)
            ),
        )
        self._schema_hash = feature_schema_hash(bundle.feature_mapping.feature_ids)

    def predict(self, extraction: FeatureExtractionResult) -> PredictionOutput:
        limitations = EXPERIMENTAL_LIMITATIONS if self._experimental_enabled else ""
        if extraction.missing_critical:
            return PredictionOutput(
                parts=TaskPrediction(None, None, False),
                labour=TaskPrediction(None, None, False),
                models_available=False,
                inference_mode=self._inference_mode,
                experimental_enabled=self._experimental_enabled,
                limitations=limitations,
            )

        if not _ml_deps_available():
            return PredictionOutput(
                parts=TaskPrediction(None, None, False),
                labour=TaskPrediction(None, None, False),
                models_available=False,
                inference_mode=self._inference_mode,
                experimental_enabled=self._experimental_enabled,
                limitations=limitations,
            )

        try:
            parts_entry = self._registry.get_active_entry(
                "parts_cost",
                expected_schema_hash=self._schema_hash,
                inference_mode=self._inference_mode,
            )
            labour_entry = self._registry.get_active_entry(
                "labour_hours",
                expected_schema_hash=self._schema_hash,
                inference_mode=self._inference_mode,
            )
        except FinancialModelError:
            return PredictionOutput(
                parts=TaskPrediction(None, None, False),
                labour=TaskPrediction(None, None, False),
                models_available=False,
                inference_mode=self._inference_mode,
                experimental_enabled=self._experimental_enabled,
                limitations=limitations,
            )

        if not parts_entry or not labour_entry:
            return PredictionOutput(
                parts=TaskPrediction(None, None, False),
                labour=TaskPrediction(None, None, False),
                models_available=False,
                inference_mode=self._inference_mode,
                experimental_enabled=self._experimental_enabled,
                limitations=limitations,
            )

        row = dict(extraction.features)
        try:
            parts_val = _predict_with_model(
                self._registry.root,
                parts_entry.model_path,
                parts_entry.preprocessor_path,
                row,
            )
            labour_val = _predict_with_model(
                self._registry.root,
                labour_entry.model_path,
                labour_entry.preprocessor_path,
                row,
            )
        except Exception as exc:
            raise FinancialDependencyError(f"Prediction failed: {exc}") from exc

        def _task_pred(entry, value: Decimal) -> TaskPrediction:
            return TaskPrediction(
                value=value,
                model_version=entry.version,
                available=True,
                algorithm=entry.algorithm or None,
                lifecycle=entry.lifecycle,
                synthetic_data=bool(entry.synthetic_data),
            )

        return PredictionOutput(
            parts=_task_pred(parts_entry, parts_val),
            labour=_task_pred(labour_entry, labour_val),
            models_available=True,
            inference_mode=self._inference_mode,
            experimental_enabled=self._experimental_enabled,
            limitations=limitations,
        )

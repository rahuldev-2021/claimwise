"""Smoke-test Gate 2 experimental artifacts (no production promotion)."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import Settings
from app.modules.financial_validation.config.loader import load_financial_config
from app.modules.financial_validation.models.model_registry import ModelRegistry, feature_schema_hash
from app.modules.financial_validation.services.prediction_service import PredictionService
from app.modules.financial_validation.training.artifact_verify import verify_trained_artifacts


def main() -> int:
    root = Path("data/financial_models/synthetic_v1/experimental_artifacts")
    registry = ModelRegistry(root)
    bundle = load_financial_config("config/financial")
    expected_hash = feature_schema_hash(bundle.feature_mapping.feature_ids)
    results: dict[str, object] = {"verified": []}

    for task in ("parts_cost", "labour_hours"):
        entries = [e for e in registry.load() if e.task == task]
        entry = entries[-1] if entries else None
        if not entry:
            print(json.dumps({"error": f"no entry for {task}"}))
            return 1
        assert not entry.eligible_for_inference()
        assert entry.eligible_for_experimental_inference()
        sample = {
            "vehicle_make": "ACME",
            "vehicle_model": "Sedan",
            "model_year": 2019,
            "vehicle_age": 5,
            "mileage": 40000,
            "repair_category": "ENGINE",
            "part_description": "Chain kit",
            "repair_action": "Replacement",
            "currency": "USD",
            "price_year": 2024,
        }
        v = verify_trained_artifacts(
            registry_root=root,
            model_rel=entry.model_path,
            preprocessor_rel=entry.preprocessor_path,
            feature_ids=bundle.feature_mapping.feature_ids,
            feature_cols=list(bundle.feature_mapping.training_columns().keys()),
            sample_feature_row=sample,
        )
        assert entry.feature_schema_hash == expected_hash
        results["verified"].append({"task": task, **v})

    prod = PredictionService(bundle, Settings(FINANCIAL_MODEL_REGISTRY_DIR="data/financial_models"))
    assert prod._inference_mode == "production"  # noqa: SLF001
    exp = PredictionService(
        bundle,
        Settings(
            FINANCIAL_EXPERIMENTAL_MODELS_ENABLED=True,
            FINANCIAL_EXPERIMENTAL_REGISTRY_DIR=str(root),
        ),
    )
    assert exp._experimental_enabled  # noqa: SLF001
    results["experimental_mode_enabled"] = True
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

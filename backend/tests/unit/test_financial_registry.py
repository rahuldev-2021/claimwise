from pathlib import Path

import pytest

from app.modules.financial_validation.models.model_registry import (
    ModelRegistry,
    ModelRegistryEntry,
    feature_schema_hash,
)


def test_registry_save_load_roundtrip(tmp_path):
    registry = ModelRegistry(tmp_path)
    entry = ModelRegistryEntry(
        task="parts_cost",
        version="v1",
        model_path="parts_cost/v1/model.joblib",
        preprocessor_path="parts_cost/v1/preprocessor.joblib",
        feature_schema_hash="abc",
        sklearn_version="1.4",
        training_data_version="test.csv",
        evaluation_strategy="group_kfold",
        metrics={},
        status="stub",
    )
    registry.save([entry])
    loaded = registry.load()
    assert len(loaded) == 1
    assert loaded[0].task == "parts_cost"


def test_registry_rejects_untrusted_path(tmp_path):
    registry = ModelRegistry(tmp_path)
    entry = ModelRegistryEntry(
        task="parts_cost",
        version="v1",
        model_path="../outside/model.joblib",
        preprocessor_path="parts_cost/v1/preprocessor.joblib",
        feature_schema_hash="abc",
        sklearn_version="1.4",
        training_data_version="test.csv",
        evaluation_strategy="x",
        metrics={},
        status="trained",
        production_ready=True,
        lifecycle="production",
    )
    (tmp_path / "parts_cost/v1").mkdir(parents=True)
    (tmp_path / "parts_cost/v1/preprocessor.joblib").write_text("x")
    registry.save([entry])
    with pytest.raises(Exception):
        registry.get_active_entry("parts_cost")


def test_feature_schema_hash_stable():
    h1 = feature_schema_hash(["a", "b"])
    h2 = feature_schema_hash(["b", "a"])
    assert h1 == h2

from pathlib import Path

from app.modules.financial_validation.models.model_registry import ModelRegistry, ModelRegistryEntry


def test_experimental_synthetic_not_eligible_for_inference(tmp_path):
    entry = ModelRegistryEntry(
        task="parts_cost",
        version="v1",
        model_path="parts_cost/v1/model.joblib",
        preprocessor_path="parts_cost/v1/preprocessor.joblib",
        feature_schema_hash="abc",
        sklearn_version="1.4",
        training_data_version="synthetic/train.csv",
        evaluation_strategy="holdout",
        metrics={},
        status="trained",
        lifecycle="experimental",
        synthetic_data=True,
        production_ready=False,
    )
    assert entry.eligible_for_inference() is False
    assert entry.eligible_for_experimental_inference() is True


def test_validation_fixture_lifecycle_eligible(tmp_path):
    registry = ModelRegistry(tmp_path)
    entry = ModelRegistryEntry(
        task="parts_cost",
        version="v1",
        model_path="parts_cost/v1/model.joblib",
        preprocessor_path="parts_cost/v1/preprocessor.joblib",
        feature_schema_hash="abc",
        sklearn_version="1.4",
        training_data_version="tiny_training.csv",
        evaluation_strategy="x",
        metrics={},
        status="trained",
        lifecycle="validation",
        synthetic_data=True,
        production_ready=False,
    )
    registry.save([entry])
    (tmp_path / "parts_cost/v1").mkdir(parents=True)
    (tmp_path / "parts_cost/v1/model.joblib").write_bytes(b"x")
    (tmp_path / "parts_cost/v1/preprocessor.joblib").write_bytes(b"x")
    assert registry.get_active_entry("parts_cost") is not None

import pytest

pytestmark = pytest.mark.financial_ml

pandas = pytest.importorskip("pandas")

from pathlib import Path

from app.modules.financial_validation.training.train_common import (
    compare_regressor_candidates,
    load_task_split_frames,
)
from app.modules.financial_validation.config.loader import load_financial_config


@pytest.fixture()
def tiny_train_val(tmp_path):
    src = Path("tests/fixtures/financial/tiny_training.csv")
    frame = pandas.read_csv(src)
    train = frame.iloc[:7]
    val = frame.iloc[7:]
    train_path = tmp_path / "train.csv"
    val_path = tmp_path / "val.csv"
    train.to_csv(train_path, index=False)
    val.to_csv(val_path, index=False)
    return train_path, val_path


def test_preprocessor_fit_uses_train_rows_only(tiny_train_val):
    train_path, val_path = tiny_train_val
    bundle = load_financial_config("config/financial")
    splits = load_task_split_frames(
        bundle=bundle,
        train_path=train_path,
        validation_path=val_path,
        test_path=None,
        task="parts_cost",
    )
    assert len(splits.x_train) == 7
    assert len(splits.x_val) == 3


def test_compare_without_register(tiny_train_val):
    train_path, val_path = tiny_train_val
    result = compare_regressor_candidates(
        "parts_cost",
        train_path=train_path,
        validation_path=val_path,
        config_dir=Path("config/financial"),
        candidates=["dummy_mean", "ridge"],
        allow_synthetic_test=True,
        register_winner=False,
    )
    assert result["selected"]["candidate"] in ("dummy_mean", "ridge")
    assert "registration" not in result
    for row in result["candidates"]:
        if row.get("status") == "RUN":
            assert "test" not in (row.get("metrics") or {})

import pytest

from app.modules.financial_validation.training.evaluation import resolve_evaluation_strategy


def test_auto_prefers_group_when_columns_present():
    strategy, note = resolve_evaluation_strategy(
        {"strategy": "auto", "group_columns": ["vehicle_make", "vehicle_model"], "time_column": "price_year"},
        {"vehicle_make", "vehicle_model", "price_year", "parts_cost"},
    )
    assert strategy == "group_kfold"
    assert "group" in note


def test_kfold_refused_when_group_columns_present():
    with pytest.raises(ValueError, match="Refusing plain kfold"):
        resolve_evaluation_strategy(
            {"strategy": "kfold", "group_columns": ["vehicle_make"], "time_column": "price_year"},
            {"vehicle_make", "price_year"},
        )

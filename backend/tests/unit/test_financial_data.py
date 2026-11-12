from pathlib import Path

from app.modules.financial_validation.config.loader import load_financial_config
from app.modules.financial_validation.data.validation import validate_training_csv


def test_validate_tiny_synthetic_fixture():
    path = Path("tests/fixtures/financial/tiny_training.csv")
    report = validate_training_csv(path, load_financial_config("config/financial").data_dictionary)
    assert report["row_count"] == 10
    assert report["provisional"] is True

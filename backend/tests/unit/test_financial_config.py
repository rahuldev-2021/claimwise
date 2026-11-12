from pathlib import Path

import pytest

from app.modules.financial_validation.config.loader import load_financial_config
from app.modules.financial_validation.features.consistency import (
    assert_training_inference_consistency,
    validate_training_inference_consistency,
)


@pytest.fixture()
def config_dir():
    return Path("config/financial")


def test_load_provisional_config(config_dir):
    bundle = load_financial_config(config_dir)
    assert bundle.data_dictionary.provisional is True
    assert bundle.rules.provisional is True
    assert bundle.feature_mapping.provisional is True


def test_training_inference_consistency(config_dir):
    bundle = load_financial_config(config_dir)
    issues = validate_training_inference_consistency(bundle.feature_mapping)
    assert issues == []
    assert_training_inference_consistency(bundle.feature_mapping)

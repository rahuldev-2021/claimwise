"""Load financial YAML configuration without optional ML dependencies."""

from pathlib import Path

import yaml

from app.modules.financial_validation.config.models import (
    DataDictionaryConfig,
    FeatureMappingConfig,
    FinancialConfigBundle,
    RulesConfig,
    TrainingDefaultsConfig,
)
from app.modules.financial_validation.exceptions import FinancialConfigError


def _load_yaml(path: Path) -> dict:
    if not path.is_file():
        raise FinancialConfigError(f"Missing configuration file: {path}")
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise FinancialConfigError(f"Configuration file must be a mapping: {path}")
    return data


def load_financial_config(config_dir: str | Path) -> FinancialConfigBundle:
    base = Path(config_dir)
    if not base.is_dir():
        raise FinancialConfigError(f"Financial config directory not found: {base}")

    try:
        data_dictionary = DataDictionaryConfig.model_validate(
            _load_yaml(base / "data_dictionary.yaml")
        )
        feature_mapping = FeatureMappingConfig.model_validate(
            _load_yaml(base / "feature_mapping.yaml")
        )
        rules = RulesConfig.model_validate(_load_yaml(base / "rules.yaml"))
        training_defaults = TrainingDefaultsConfig.model_validate(
            _load_yaml(base / "training_defaults.yaml")
        )
    except FinancialConfigError:
        raise
    except Exception as exc:
        raise FinancialConfigError(f"Invalid financial configuration: {exc}") from exc

    return FinancialConfigBundle(
        data_dictionary=data_dictionary,
        feature_mapping=feature_mapping,
        rules=rules,
        training_defaults=training_defaults,
        config_dir=str(base.resolve()),
    )

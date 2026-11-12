"""Pydantic models for PROVISIONAL financial YAML configuration."""

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class DataDictionaryConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    provisional: bool = True
    version: str = "0.0-provisional"
    targets: dict[str, Any] = Field(default_factory=dict)
    currency: dict[str, Any] = Field(default_factory=dict)
    leakage_forbidden_columns: list[str] = Field(default_factory=list)
    fields: list[dict[str, Any]] = Field(default_factory=list)


class InferenceFeatureSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_path: Optional[str] = None
    derivation: Optional[str] = None
    required_at_inference: bool = False
    if_missing: Literal["abstain", "absent"] = "absent"


class FeatureMappingConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    provisional: bool = True
    version: str = "0.0-provisional"
    feature_ids: list[str] = Field(default_factory=list)
    training: dict[str, Any] = Field(default_factory=dict)
    inference: dict[str, Any] = Field(default_factory=dict)
    derivations: dict[str, Any] = Field(default_factory=dict)

    def inference_sources(self) -> dict[str, InferenceFeatureSource]:
        raw = (self.inference or {}).get("sources") or {}
        return {k: InferenceFeatureSource.model_validate(v) for k, v in raw.items()}

    def training_columns(self) -> dict[str, str]:
        return dict((self.training or {}).get("columns") or {})


class RulesConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    provisional: bool = True
    version: str = "0.0-provisional"
    currency: dict[str, Any] = Field(default_factory=dict)
    discrepancy_bands: dict[str, Any] = Field(default_factory=dict)
    abstain: dict[str, str] = Field(default_factory=dict)
    availability: dict[str, Any] = Field(default_factory=dict)
    rule_ids: list[str] = Field(default_factory=list)


class TrainingDefaultsConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    provisional: bool = True
    version: str = "0.0-provisional"
    random_seed: int = 42
    evaluation: dict[str, Any] = Field(default_factory=dict)
    model_candidates: dict[str, list[str]] = Field(default_factory=dict)
    registry: dict[str, Any] = Field(default_factory=dict)


class FinancialConfigBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data_dictionary: DataDictionaryConfig
    feature_mapping: FeatureMappingConfig
    rules: RulesConfig
    training_defaults: TrainingDefaultsConfig
    config_dir: str

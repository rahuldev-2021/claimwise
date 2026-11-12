"""Training vs inference feature consistency checks."""

from app.modules.financial_validation.config.models import FeatureMappingConfig
from app.modules.financial_validation.exceptions import FinancialFeatureError


def validate_training_inference_consistency(mapping: FeatureMappingConfig) -> list[str]:
    """Return list of issues; empty if training features are inferable."""
    issues: list[str] = []
    training_features = set(mapping.training_columns().keys())
    inference_sources = mapping.inference_sources()
    inferable: set[str] = set()
    for fid, src in inference_sources.items():
        if src.claim_path or src.derivation:
            inferable.add(fid)

    derivations = set((mapping.derivations or {}).keys())
    for feature_id in training_features:
        if feature_id in inferable:
            continue
        if feature_id in inference_sources and (
            inference_sources[feature_id].claim_path
            or inference_sources[feature_id].derivation
        ):
            continue
        issues.append(f"Training feature {feature_id!r} has no inference source or derivation")

    for fid, src in inference_sources.items():
        if src.derivation and src.derivation not in derivations:
            issues.append(f"Inference feature {fid!r} references unknown derivation {src.derivation!r}")

    return issues


def assert_training_inference_consistency(mapping: FeatureMappingConfig) -> None:
    issues = validate_training_inference_consistency(mapping)
    if issues:
        raise FinancialFeatureError("; ".join(issues))

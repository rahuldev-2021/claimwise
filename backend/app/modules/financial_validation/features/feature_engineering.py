"""Claim-based inference feature extraction (no pandas/sklearn required)."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from app.modules.financial_validation.config.models import FeatureMappingConfig
from app.modules.financial_validation.exceptions import FinancialFeatureError
from app.modules.financial_validation.features.vehicle_category_lookup import lookup_vehicle_category
from app.schemas.claim import ClaimInput


@dataclass
class FeatureExtractionResult:
    features: dict[str, Any] = field(default_factory=dict)
    missing_critical: list[str] = field(default_factory=list)
    missing_optional: list[str] = field(default_factory=list)
    abstain_reasons: list[str] = field(default_factory=list)


def _get_path(obj: Any, path: str) -> Any:
    cur = obj
    for part in path.split("."):
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            cur = getattr(cur, part, None)
    return cur


def _apply_derivation(name: str, spec: dict[str, Any], claim: ClaimInput) -> Any:
    dtype = spec.get("type")
    if dtype == "year_delta":
        year = _get_path(claim, spec["year_claim_path"])
        ref: datetime = _get_path(claim, spec["reference_claim_path"])
        if year is None or ref is None:
            return None
        return ref.year - int(year)
    if dtype == "year_from_datetime":
        ref = _get_path(claim, spec["reference_claim_path"])
        if ref is None:
            return None
        return ref.year
    if dtype == "vehicle_category_from_claim_or_lookup":
        cat = _get_path(claim, "vehicle.vehicle_category")
        if cat:
            return str(cat).strip().upper()
        make = _get_path(claim, "vehicle.make")
        model = _get_path(claim, "vehicle.model")
        if make and model:
            return lookup_vehicle_category(str(make), str(model))
        return None
    if dtype == "repair_complexity_from_action":
        action = (_get_path(claim, "recommended_repair.recommended_action") or "").lower()
        if not action:
            return None
        if any(w in action for w in ("overhaul", "replace", "replacement")):
            if any(w in action for w in ("engine", "transmission", "clutch", "assembly")):
                return "HIGH"
            return "MEDIUM"
        if any(w in action for w in ("resurface", "rebuild", "reseal")):
            return "MEDIUM"
        if any(w in action for w in ("repair", "adjust", "flush", "service")):
            return "LOW"
        return "MEDIUM"
    raise FinancialFeatureError(f"Unknown derivation type: {dtype!r} for {name!r}")


def extract_inference_features(
    claim: ClaimInput,
    mapping: FeatureMappingConfig,
) -> FeatureExtractionResult:
    result = FeatureExtractionResult()
    sources = mapping.inference_sources()
    derivations = mapping.derivations or {}

    for feature_id, src in sources.items():
        value: Any = None
        if src.claim_path:
            value = _get_path(claim, src.claim_path)
        elif src.derivation:
            value = _apply_derivation(src.derivation, derivations[src.derivation], claim)

        if value is None or (isinstance(value, str) and not value.strip()):
            if src.required_at_inference:
                result.missing_critical.append(feature_id)
                if src.if_missing == "abstain":
                    result.abstain_reasons.append(f"missing_required:{feature_id}")
            else:
                result.missing_optional.append(feature_id)
            continue

        if isinstance(value, str):
            value = value.strip()
        result.features[feature_id] = value

    return result


def training_feature_ids(mapping: FeatureMappingConfig) -> set[str]:
    return set(mapping.training_columns().keys())


def inferable_feature_ids(mapping: FeatureMappingConfig) -> set[str]:
    ids: set[str] = set()
    for fid, src in mapping.inference_sources().items():
        if src.claim_path or src.derivation:
            ids.add(fid)
    return ids

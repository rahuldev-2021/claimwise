"""Prepare claim + deterministic NLP context for LLM fallback."""

import json

from app.modules.nlp.entity_confidence import is_confirmed_entity
from app.modules.nlp.schemas import NLPAnalysisResult, TextSourceField
from app.schemas.claim import ClaimInput

_MAX_CANONICALS_PER_FIELD = 20


def build_nlp_llm_context(claim: ClaimInput, deterministic: NLPAnalysisResult) -> str:
    by_field: dict[str, list[str]] = {}
    confirmed_count = 0
    for ext in deterministic.field_extractions:
        for e in ext.entities:
            if not is_confirmed_entity(e):
                continue
            confirmed_count += 1
            field_key = e.source_field.value
            bucket = by_field.setdefault(field_key, [])
            if e.canonical not in bucket:
                bucket.append(e.canonical)

    coverage: dict[str, object] = {"confirmed_entity_count": confirmed_count, "by_field": {}}
    field_map: dict[str, object] = {}
    for field_key, canonicals in by_field.items():
        clipped = canonicals[:_MAX_CANONICALS_PER_FIELD]
        field_map[field_key] = {
            "canonicals": clipped,
            "additional_canonical_count": max(0, len(canonicals) - len(clipped)),
        }
    coverage["by_field"] = field_map

    payload = {
        "vehicle": {
            "make": claim.vehicle.make,
            "model": claim.vehicle.model,
            "model_year": claim.vehicle.model_year,
            "mileage": claim.vehicle.mileage,
        },
        "repair_category": claim.recommended_repair.repair_category,
        "source_fields": {
            TextSourceField.CUSTOMER_COMPLAINT.value: deterministic.original_complaint,
            TextSourceField.TECHNICIAN_DIAGNOSIS.value: deterministic.original_diagnosis,
            TextSourceField.RECOMMENDED_REPAIR.value: deterministic.original_repair,
        },
        "deterministic_coverage": coverage,
        "deterministic_relationship_count": len(deterministic.entity_relationships),
        "missing_information": [
            {"code": m.code, "message": m.message, "severity": m.severity.value}
            for m in deterministic.missing_information
        ],
    }
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)

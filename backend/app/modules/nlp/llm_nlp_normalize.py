"""Coerce common LLM enum drift before strict schema validation."""

from __future__ import annotations

from app.modules.nlp.schemas import EntityCategory, RelationshipCertainty, TextSourceField

_VALID_CATEGORIES = {e.value for e in EntityCategory}
_VALID_CERTAINTY = {e.value for e in RelationshipCertainty}
_VALID_SOURCE_FIELDS = {e.value for e in TextSourceField}

_CATEGORY_ALIASES: dict[str, str] = {
    "condition": EntityCategory.OPERATING_CONDITION.value,
    "conditions": EntityCategory.OPERATING_CONDITION.value,
    "operating_conditions": EntityCategory.OPERATING_CONDITION.value,
    "action": EntityCategory.REPAIR_ACTION.value,
    "actions": EntityCategory.REPAIR_ACTION.value,
    "repair": EntityCategory.REPAIR_ACTION.value,
    "diagnostic_procedure": EntityCategory.DIAGNOSTIC.value,
    "diagnostic_method": EntityCategory.DIAGNOSTIC.value,
    "procedure": EntityCategory.DIAGNOSTIC.value,
    "test": EntityCategory.DIAGNOSTIC.value,
    "finding": EntityCategory.DIAGNOSTIC_FINDING.value,
    "findings": EntityCategory.DIAGNOSTIC_FINDING.value,
    "symptoms": EntityCategory.SYMPTOM.value,
    "component_name": EntityCategory.COMPONENT.value,
    "part_name": EntityCategory.PART.value,
    "dtc": EntityCategory.DTC_CODE.value,
    "code": EntityCategory.DTC_CODE.value,
}

_CERTAINTY_ALIASES: dict[str, str] = {
    "conditional": RelationshipCertainty.REPORTED.value,
    "recommended": RelationshipCertainty.REPORTED.value,
    "optional": RelationshipCertainty.REPORTED.value,
    "possible": RelationshipCertainty.SUSPECTED.value,
    "probable": RelationshipCertainty.SUSPECTED.value,
    "verified": RelationshipCertainty.CONFIRMED.value,
}

_SOURCE_FIELD_ALIASES: dict[str, str] = {
    "complaint": TextSourceField.CUSTOMER_COMPLAINT.value,
    "customer_complaints": TextSourceField.CUSTOMER_COMPLAINT.value,
    "diagnosis": TextSourceField.TECHNICIAN_DIAGNOSIS.value,
    "technician_diagnostic": TextSourceField.TECHNICIAN_DIAGNOSIS.value,
    "repair": TextSourceField.RECOMMENDED_REPAIR.value,
    "recommended_repairs": TextSourceField.RECOMMENDED_REPAIR.value,
}


def _normalize_category(raw: object) -> str | None:
    if not isinstance(raw, str):
        return None
    key = raw.strip().lower().replace(" ", "_").replace("-", "_")
    if key in _VALID_CATEGORIES:
        return key
    return _CATEGORY_ALIASES.get(key)


def _normalize_certainty(raw: object) -> str | None:
    if raw is None:
        return RelationshipCertainty.REPORTED.value
    if not isinstance(raw, str):
        return None
    key = raw.strip().lower()
    if key in _VALID_CERTAINTY:
        return key
    return _CERTAINTY_ALIASES.get(key)


def _normalize_source_field(raw: object) -> str | None:
    if not isinstance(raw, str):
        return None
    key = raw.strip().lower().replace(" ", "_")
    if key in _VALID_SOURCE_FIELDS:
        return key
    return _SOURCE_FIELD_ALIASES.get(key)


def normalize_llm_nlp_payload(data: dict) -> tuple[dict, list[str]]:
    """Return a copy safe for LLMNlpExtractionResponse.model_validate; notes dropped rows."""
    notes: list[str] = []
    entities_in = data.get("entities") if isinstance(data.get("entities"), list) else []
    entities_out: list[dict] = []
    for idx, row in enumerate(entities_in):
        if not isinstance(row, dict):
            notes.append(f"dropped_entity:{idx}:not_object")
            continue
        cat = _normalize_category(row.get("category"))
        field = _normalize_source_field(row.get("source_field"))
        if not cat or not field:
            notes.append(f"dropped_entity:{row.get('temp_id', idx)}:bad_enum")
            continue
        ent = dict(row)
        ent["category"] = cat
        ent["source_field"] = field
        entities_out.append(ent)

    kept_ids = {e.get("temp_id") for e in entities_out if e.get("temp_id")}
    rels_in = data.get("relationships") if isinstance(data.get("relationships"), list) else []
    rels_out: list[dict] = []
    for idx, row in enumerate(rels_in):
        if not isinstance(row, dict):
            notes.append(f"dropped_rel:{idx}:not_object")
            continue
        cert = _normalize_certainty(row.get("certainty"))
        field = _normalize_source_field(row.get("source_field"))
        sub, obj = row.get("subject_temp_id"), row.get("object_temp_id")
        if not cert or not field or sub not in kept_ids or obj not in kept_ids:
            notes.append(f"dropped_rel:{idx}:bad_ref_or_enum")
            continue
        rel = dict(row)
        rel["certainty"] = cert
        rel["source_field"] = field
        rels_out.append(rel)

    obs_in = data.get("observations") if isinstance(data.get("observations"), list) else []
    obs_out = [o for o in obs_in if isinstance(o, dict) and o.get("code") and o.get("message")]

    return {
        "entities": entities_out,
        "relationships": rels_out,
        "observations": obs_out,
    }, notes

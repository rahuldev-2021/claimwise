"""Validate LLM NLP JSON against schema and source grounding."""

from __future__ import annotations

import json
import re

from pydantic import ValidationError

from app.modules.nlp.llm_nlp_normalize import normalize_llm_nlp_payload
from app.modules.nlp.llm_nlp_schemas import LLMNlpExtractionResponse
from app.modules.nlp.schemas import EntityCategory, TextSourceField
from app.modules.nlp.taxonomy_data import TAXONOMY_ALIASES


_DTC_RE = re.compile(r"^P\d{4}$", re.I)
_MEASUREMENT_RE = re.compile(r"\d", re.I)


def _canonical_allowed(category: str, canonical: str) -> bool:
    bucket = TAXONOMY_ALIASES.get(category, {})
    return canonical in bucket


def validate_llm_nlp_response(
    raw: str,
    *,
    originals: dict[TextSourceField, str],
) -> tuple[LLMNlpExtractionResponse | None, list[str]]:
    errors: list[str] = []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, [f"invalid_json: {exc}"]

    if not isinstance(data, dict):
        return None, ["schema: root must be an object"]

    normalized, coerce_notes = normalize_llm_nlp_payload(data)
    errors.extend(coerce_notes)

    try:
        parsed = LLMNlpExtractionResponse.model_validate(normalized)
    except ValidationError as exc:
        return None, [f"schema: {exc}"]

    ids = {e.temp_id for e in parsed.entities}
    for ent in parsed.entities:
        field_text = originals.get(ent.source_field, "")
        if not ent.source_excerpt or ent.source_excerpt.lower() not in field_text.lower():
            errors.append(f"ungrounded_excerpt: {ent.temp_id}")
        if ent.category == EntityCategory.DTC_CODE and not _DTC_RE.match(ent.canonical):
            errors.append(f"invented_dtc: {ent.temp_id}")
        if ent.category == EntityCategory.MEASUREMENT and not _MEASUREMENT_RE.search(
            ent.source_excerpt
        ):
            errors.append(f"invented_measurement: {ent.temp_id}")
        cat = ent.category.value
        if cat in TAXONOMY_ALIASES and not _canonical_allowed(cat, ent.canonical):
            errors.append(f"unsupported_canonical: {ent.temp_id}/{ent.canonical}")
        if ent.span_start is not None and ent.span_end is not None:
            if ent.span_end <= ent.span_start or ent.span_end > len(field_text):
                errors.append(f"invalid_span: {ent.temp_id}")

    for rel in parsed.relationships:
        if rel.subject_temp_id not in ids or rel.object_temp_id not in ids:
            errors.append(f"invalid_rel_ref: {rel.subject_temp_id}->{rel.object_temp_id}")
        field_text = originals.get(rel.source_field, "")
        if rel.source_excerpt.lower() not in field_text.lower():
            errors.append(f"ungrounded_rel_excerpt: {rel.subject_temp_id}")

    if errors:
        return None, errors
    return parsed, []

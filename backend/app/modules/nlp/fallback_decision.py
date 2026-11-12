"""Configurable fallback decision for optional LLM NLP enrichment."""

from __future__ import annotations

import re

from app.core.config import Settings
from app.modules.nlp.entity_confidence import confirmed_entities, is_confirmed_entity
from app.modules.nlp.schemas import (
    EntityCategory,
    ExtractionMethod,
    LLMFallbackDecision,
    NLPAnalysisResult,
    RelationshipPredicate,
    TextSourceField,
)
from app.modules.nlp.taxonomy import normalize_term
from app.schemas.claim import ClaimInput

_SUSPECT = re.compile(r"\bsuspect(?:ed|s)?\b|\bpossible\b|\blikely\b", re.I)
_CONFIRMED = re.compile(r"\bconfirmed\b", re.I)


def evaluate_fallback(
    claim: ClaimInput,
    result: NLPAnalysisResult,
    settings: Settings,
) -> LLMFallbackDecision:
    mode = (settings.LLM_NLP_FALLBACK_MODE or "conditional").strip().lower()
    if mode == "off":
        return LLMFallbackDecision(considered=False, triggered=False)
    if mode == "always":
        return LLMFallbackDecision(
            considered=True,
            triggered=True,
            trigger_codes=["FORCED_EVAL_MODE"],
            min_trigger_count_met=True,
        )

    codes: list[str] = []
    min_count = max(1, settings.LLM_NLP_MIN_TRIGGER_COUNT)

    all_confirmed = [
        e
        for ext in result.field_extractions
        for e in ext.entities
        if is_confirmed_entity(e)
    ]
    fuzzy_ents = [
        e
        for ext in result.field_extractions
        for e in ext.entities
        if e.extraction_method == ExtractionMethod.FUZZY and is_confirmed_entity(e)
    ]
    if fuzzy_ents:
        codes.append("AMBIGUOUS_TERMINOLOGY")

    if _has_conflicting_canonicals(all_confirmed):
        codes.append("CONFLICTING_CANONICALS")

    if _negation_certainty_complexity(result, claim):
        codes.append("NEGATION_CERTAINTY_COMPLEXITY")

    if _repair_action_ambiguity(result):
        codes.append("REPAIR_ACTION_AMBIGUITY")

    if _rich_text_low_structure(claim, all_confirmed):
        codes.append("RICH_TEXT_LOW_STRUCTURE")

    triggered = len(codes) >= min_count
    return LLMFallbackDecision(
        considered=True,
        triggered=triggered,
        trigger_codes=codes,
        min_trigger_count_met=triggered,
    )


def _has_conflicting_canonicals(entities) -> bool:
    by_span: dict[tuple[TextSourceField, int, int], set[str]] = {}
    for e in entities:
        if e.span_start is None or e.span_end is None:
            continue
        key = (e.source_field, e.span_start, e.span_end)
        by_span.setdefault(key, set()).add(e.canonical)
    return any(len(v) > 1 for v in by_span.values())


def _negation_certainty_complexity(result: NLPAnalysisResult, claim: ClaimInput) -> bool:
    diag = claim.technician_diagnosis
    has_negated_failure = any(
        e.category == EntityCategory.FAILURE_MODE and e.negated
        for ext in result.field_extractions
        if ext.source_field == TextSourceField.TECHNICIAN_DIAGNOSIS
        for e in ext.entities
        if is_confirmed_entity(e)
    )
    mixed = (_SUSPECT.search(diag) or _CONFIRMED.search(diag)) and has_negated_failure
    return bool(mixed)


def _repair_action_ambiguity(result: NLPAnalysisResult) -> bool:
    repair_ents = confirmed_entities(result.recommended_repair.entities)
    actions = [e for e in repair_ents if e.category == EntityCategory.REPAIR_ACTION]
    if len(actions) < 2:
        return False
    rec_rel = [
        r
        for r in result.entity_relationships
        if r.source_field == TextSourceField.RECOMMENDED_REPAIR
        and r.predicate == RelationshipPredicate.RECOMMENDS
    ]
    return len(rec_rel) < len(actions)


def _rich_text_low_structure(claim: ClaimInput, confirmed: list) -> bool:
    blobs = [
        (TextSourceField.CUSTOMER_COMPLAINT, claim.customer_complaint),
        (TextSourceField.TECHNICIAN_DIAGNOSIS, claim.technician_diagnosis),
    ]
    for field, text in blobs:
        words = len(text.split())
        if words < 25:
            continue
        ent_count = sum(1 for e in confirmed if e.source_field == field)
        if ent_count >= words // 8:
            continue
        for token in re.findall(r"[a-z]{4,}", text.lower()):
            cat, canonical, _ = normalize_term(token, None)
            if cat != "unknown" and not any(
                e.source_field == field and e.canonical == canonical for e in confirmed
            ):
                return True
    return False

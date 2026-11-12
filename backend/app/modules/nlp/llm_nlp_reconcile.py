"""Merge validated LLM entities into deterministic NLP output."""

from __future__ import annotations

from app.modules.nlp.entity_ids import assign_entity_ids
from app.modules.nlp.llm_nlp_schemas import LLMNlpExtractionResponse
from app.modules.nlp.schemas import (
    EntityCategory,
    EntityRelationship,
    ExtractionMethod,
    ExtractedEntity,
    MatchMethod,
    NLPAnalysisResult,
    ReconciliationConflict,
    RelationshipPredicate,
    TextSourceField,
)
from app.modules.nlp.entity_confidence import is_confirmed_entity


def reconcile_llm_extraction(
    deterministic: NLPAnalysisResult,
    llm: LLMNlpExtractionResponse,
) -> tuple[NLPAnalysisResult, list[ReconciliationConflict]]:
    conflicts: list[ReconciliationConflict] = []
    temp_to_id: dict[str, str] = {}

    by_field: dict[TextSourceField, list[ExtractedEntity]] = {}
    for ext in deterministic.field_extractions:
        by_field[ext.source_field] = list(ext.entities)

    for ent in llm.entities:
        field_list = by_field.setdefault(ent.source_field, [])
        if _duplicate_entity(field_list, ent):
            continue
        conflict = _find_conflict(field_list, ent)
        if conflict:
            conflicts.append(conflict)
            continue
        new_ent = ExtractedEntity(
            text=ent.text,
            canonical=ent.canonical,
            category=ent.category,
            source_field=ent.source_field,
            span_start=ent.span_start,
            span_end=ent.span_end,
            source_text=ent.source_excerpt,
            negated=ent.negated,
            match_method=MatchMethod.EXACT,
            extraction_method=ExtractionMethod.LLM,
            confidence=ent.confidence,
            source_certainty=ent.source_certainty,
            llm_reconciled=True,
        )
        field_list.append(new_ent)

    for ext in deterministic.field_extractions:
        ext.entities = by_field.get(ext.source_field, ext.entities)

    repair_entities = by_field.get(
        TextSourceField.RECOMMENDED_REPAIR, deterministic.recommended_repair.entities
    )
    deterministic = deterministic.model_copy(
        update={
            "recommended_repair": deterministic.recommended_repair.model_copy(
                update={"entities": repair_entities}
            )
        }
    )

    assign_entity_ids(deterministic.field_extractions)
    for ent in llm.entities:
        for field_ent in by_field.get(ent.source_field, []):
            if field_ent.llm_reconciled and field_ent.canonical == ent.canonical:
                temp_to_id[ent.temp_id] = field_ent.entity_id

    new_rels: list[EntityRelationship] = list(deterministic.entity_relationships)
    rel_counter = len(new_rels) + 1
    for rel in llm.relationships:
        sub = temp_to_id.get(rel.subject_temp_id)
        obj = temp_to_id.get(rel.object_temp_id)
        if not sub or not obj:
            continue
        new_rels.append(
            EntityRelationship(
                relationship_id=f"REL-{rel_counter:03d}",
                subject_entity_id=sub,
                predicate=rel.predicate,
                object_entity_id=obj,
                source_field=rel.source_field,
                source_text=rel.source_excerpt[:500],
                confidence=rel.confidence or 0.75,
                extraction_method=ExtractionMethod.LLM,
                polarity=rel.polarity,
                certainty=rel.certainty,
            )
        )
        rel_counter += 1

    merged = deterministic.model_copy(update={"entity_relationships": new_rels})
    return merged, conflicts


def _duplicate_entity(existing: list[ExtractedEntity], ent) -> bool:
    for e in existing:
        if (
            e.source_field == ent.source_field
            and e.category == ent.category
            and e.canonical == ent.canonical
        ):
            if e.span_start is not None and ent.span_start is not None:
                if e.span_start == ent.span_start and e.span_end == ent.span_end:
                    return True
            elif is_confirmed_entity(e):
                return True
    return False


def _find_conflict(
    existing: list[ExtractedEntity], ent
) -> ReconciliationConflict | None:
    for e in existing:
        if not is_confirmed_entity(e):
            continue
        if e.source_field != ent.source_field:
            continue
        if e.span_start is None or ent.span_start is None:
            continue
        if (
            e.span_start == ent.span_start
            and e.span_end == ent.span_end
            and e.canonical != ent.canonical
        ):
            return ReconciliationConflict(
                field=ent.source_field.value,
                deterministic_ref=f"{e.entity_id}:{e.canonical}",
                llm_ref=f"{ent.temp_id}:{ent.canonical}",
                resolution="kept_deterministic",
            )
    return None

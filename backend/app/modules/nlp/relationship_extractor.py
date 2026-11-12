"""Phrase-local relationship extraction with provenance."""

from __future__ import annotations

import re

from app.modules.nlp.entity_confidence import is_confirmed_entity
from app.modules.nlp.schemas import (
    EntityCategory,
    EntityRelationship,
    ExtractionMethod,
    ExtractedEntity,
    RelationshipCertainty,
    RelationshipPolarity,
    RelationshipPredicate,
    TextSourceField,
)

_NOISE_FROM = re.compile(
    r"(?P<symptom>rattl(?:e|ing)|squeal(?:ing)?|knock(?:ing)?|clunk(?:ing)?|noise)"
    r".{0,40}?\bfrom\b.{0,5}(?:the\s+)?(?P<comp>engine|exhaust|transmission|brake)",
    re.IGNORECASE,
)
_ORIGINATES = re.compile(
    r"(?:originat(?:e|ing|es)|comes)\s+from.{0,30}?(?P<comp>engine|exhaust|timing)",
    re.IGNORECASE,
)
_CONFIRMED = re.compile(r"\bconfirmed\b", re.IGNORECASE)
_SUSPECT = re.compile(r"\bsuspect(?:ed|s)?\b|\bpossible\b|\blikely\b", re.IGNORECASE)


def _certainty_for_clause(clause: str) -> RelationshipCertainty:
    if _CONFIRMED.search(clause):
        return RelationshipCertainty.CONFIRMED
    if _SUSPECT.search(clause):
        return RelationshipCertainty.SUSPECTED
    return RelationshipCertainty.REPORTED


def _entity_by_canonical(
    entities: list[ExtractedEntity], canonical: str, category: EntityCategory
) -> ExtractedEntity | None:
    for ent in entities:
        if ent.canonical == canonical and ent.category == category and not ent.negated:
            return ent
    return None


def _entity_by_category(
    entities: list[ExtractedEntity],
    category: EntityCategory,
    *,
    confirmed_only: bool = False,
) -> list[ExtractedEntity]:
    out = [e for e in entities if e.category == category and not e.negated and e.entity_id]
    if confirmed_only:
        out = [e for e in out if is_confirmed_entity(e)]
    return out


def extract_relationships(
    field_extractions: list,
    *,
    originals: dict[TextSourceField, str],
) -> list[EntityRelationship]:
    rels: list[EntityRelationship] = []
    rel_counter = 1

    by_field: dict[TextSourceField, list[ExtractedEntity]] = {}
    for ext in field_extractions:
        by_field[ext.source_field] = list(ext.entities)

    for source, ents in by_field.items():
        original = originals.get(source, "")
        text = original or " ".join(e.text for e in ents)

        clauses = re.split(r"(?<=[.;])\s+|\s+but\s+|\s+however\s+", text, flags=re.IGNORECASE)
        for clause in clauses:
            clause = clause.strip()
            if not clause:
                continue
            certainty = _certainty_for_clause(clause)

            for match in _NOISE_FROM.finditer(clause):
                symptom_ent = _match_symptom(ents, match.group("symptom"))
                comp_ent = _match_component(ents, match.group("comp"))
                if symptom_ent and comp_ent:
                    rels.append(
                        _rel(
                            rel_counter,
                            symptom_ent,
                            RelationshipPredicate.LOCATED_AT,
                            comp_ent,
                            source,
                            match.group(0),
                            certainty,
                        )
                    )
                    rel_counter += 1

            for match in _ORIGINATES.finditer(clause):
                comp_ent = _match_component(ents, match.group("comp"))
                symptoms = _entity_by_category(ents, EntityCategory.SYMPTOM)
                if comp_ent and symptoms:
                    rels.append(
                        _rel(
                            rel_counter,
                            symptoms[0],
                            RelationshipPredicate.LOCATED_AT,
                            comp_ent,
                            source,
                            match.group(0),
                            certainty,
                        )
                    )
                    rel_counter += 1

    complaint = by_field.get(TextSourceField.CUSTOMER_COMPLAINT, [])
    diagnosis = by_field.get(TextSourceField.TECHNICIAN_DIAGNOSIS, [])
    repair_ents = by_field.get(TextSourceField.RECOMMENDED_REPAIR, [])


    for fail in _entity_by_category(diagnosis, EntityCategory.FAILURE_MODE, confirmed_only=True):
        for comp in _entity_by_category(diagnosis, EntityCategory.COMPONENT, confirmed_only=True):
            if fail.source_field == comp.source_field:
                rels.append(
                    _rel(
                        rel_counter,
                        fail,
                        RelationshipPredicate.TARGETS,
                        comp,
                        TextSourceField.TECHNICIAN_DIAGNOSIS,
                        fail.source_text or fail.text,
                        _certainty_for_clause(fail.source_text or fail.text),
                    )
                )
                rel_counter += 1

    repair_original = originals.get(TextSourceField.RECOMMENDED_REPAIR, "")
    for clause in re.split(r"(?<=[.;])\s+|\s+;\s*", repair_original, flags=re.IGNORECASE):
        clause_l = clause.strip().lower()
        if not clause_l:
            continue
        certainty = _certainty_for_clause(clause_l)
        actions = [
            e
            for e in _entity_by_category(
                repair_ents, EntityCategory.REPAIR_ACTION, confirmed_only=True
            )
            if e.text.lower() in clause_l
        ]
        actions.sort(key=lambda a: clause_l.find(a.text.lower()))
        targets = _entity_by_category(
            repair_ents, EntityCategory.PART, confirmed_only=True
        ) + _entity_by_category(repair_ents, EntityCategory.COMPONENT, confirmed_only=True)
        targets.sort(
            key=lambda e: (0 if e.category == EntityCategory.PART else 1, e.span_start or 0)
        )
        for i, action in enumerate(actions):
            a_idx = clause_l.find(action.text.lower())
            if a_idx < 0:
                continue
            next_idx = len(clause_l)
            if i + 1 < len(actions):
                n_idx = clause_l.find(actions[i + 1].text.lower())
                if n_idx > a_idx:
                    next_idx = n_idx
            segment = clause_l[a_idx:next_idx]
            seg_offset = a_idx
            for part in targets:
                p_idx = segment.find(part.text.lower())
                if p_idx < 0:
                    continue
                if p_idx < len(action.text.lower()):
                    continue
                abs_start = seg_offset
                abs_end = seg_offset + p_idx + len(part.text)
                excerpt = clause.strip()[abs_start:abs_end]
                rels.append(
                    _rel(
                        rel_counter,
                        action,
                        RelationshipPredicate.RECOMMENDS,
                        part,
                        TextSourceField.RECOMMENDED_REPAIR,
                        excerpt,
                        certainty,
                    )
                )
                rel_counter += 1

    diag_original = originals.get(TextSourceField.TECHNICIAN_DIAGNOSIS, "")
    for clause in re.split(r"(?<=[.;])\s+|\s+but\s+|\s+;\s*", diag_original, flags=re.IGNORECASE):
        clause_l = clause.strip().lower()
        if not clause_l:
            continue
        certainty = _certainty_for_clause(clause)
        in_clause = [e for e in diagnosis if is_confirmed_entity(e) and e.text.lower() in clause_l]
        findings = [
            e
            for e in in_clause
            if e.category in (EntityCategory.DIAGNOSTIC_FINDING, EntityCategory.FAILURE_MODE)
        ]
        parts = [
            e
            for e in in_clause
            if e.category in (EntityCategory.PART, EntityCategory.COMPONENT)
        ]
        for finding in findings:
            if not finding.entity_id:
                continue
            for part in parts:
                if part.entity_id and part.text.lower() in clause_l:
                    rels.append(
                        _rel(
                            rel_counter,
                            finding,
                            RelationshipPredicate.AFFECTS,
                            part,
                            TextSourceField.TECHNICIAN_DIAGNOSIS,
                            finding.source_text or finding.text,
                            certainty,
                        )
                    )
                    rel_counter += 1

    return _dedupe_rels(rels)


def _rel(
    counter: int,
    subject: ExtractedEntity,
    predicate: RelationshipPredicate,
    obj: ExtractedEntity,
    source: TextSourceField,
    source_text: str,
    certainty: RelationshipCertainty,
) -> EntityRelationship:
    polarity = (
        RelationshipPolarity.NEGATIVE
        if subject.negated or obj.negated
        else RelationshipPolarity.POSITIVE
    )
    return EntityRelationship(
        relationship_id=f"REL-{counter:03d}",
        subject_entity_id=subject.entity_id,
        predicate=predicate,
        object_entity_id=obj.entity_id,
        source_field=source,
        source_text=source_text[:500],
        confidence=0.85,
        extraction_method=ExtractionMethod.RULE_BASED,
        polarity=polarity,
        certainty=certainty,
    )


def _match_symptom(ents: list[ExtractedEntity], surface: str) -> ExtractedEntity | None:
    surface = surface.lower()
    for ent in _entity_by_category(ents, EntityCategory.SYMPTOM):
        if surface in ent.text.lower() or surface in ent.canonical:
            return ent
    return _entity_by_category(ents, EntityCategory.SYMPTOM)[0] if _entity_by_category(ents, EntityCategory.SYMPTOM) else None


def _match_component(ents: list[ExtractedEntity], surface: str) -> ExtractedEntity | None:
    surface = surface.lower()
    for ent in _entity_by_category(ents, EntityCategory.COMPONENT):
        if surface in ent.text.lower() or surface in ent.canonical or surface in ent.text:
            return ent
    return _entity_by_canonical(ents, surface, EntityCategory.COMPONENT)


def _entity_by_canonical(ents: list[ExtractedEntity], hint: str, category: EntityCategory):
    hint = hint.lower()
    for ent in ents:
        if ent.category == category and hint in ent.canonical:
            return ent
    return None


def _dedupe_rels(rels: list[EntityRelationship]) -> list[EntityRelationship]:
    seen: set[tuple[str, str, str]] = set()
    out: list[EntityRelationship] = []
    for r in rels:
        key = (r.subject_entity_id, r.predicate.value, r.object_entity_id)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out

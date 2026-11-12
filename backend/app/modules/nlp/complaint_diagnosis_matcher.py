"""Compare extracted complaint and diagnosis for reviewer hints (not validity verdicts)."""

from app.modules.nlp.entity_confidence import is_confirmed_entity
from app.modules.nlp.schemas import (
    ComplaintDiagnosisComparison,
    FieldExtraction,
    SymptomDiagnosisPair,
    TextSourceField,
)
from app.modules.nlp.taxonomy_data import HEAVY_REPAIR_TERMS, LIGHT_REPAIR_TERMS
from app.schemas.claim import ClaimInput


def compare_complaint_and_diagnosis(
    claim: ClaimInput,
    field_extractions: list[FieldExtraction],
) -> ComplaintDiagnosisComparison:
    complaint_ents = _entities(field_extractions, TextSourceField.CUSTOMER_COMPLAINT)
    diagnosis_ents = _entities(field_extractions, TextSourceField.TECHNICIAN_DIAGNOSIS)

    complaint_components = {
        e.canonical
        for e in complaint_ents
        if is_confirmed_entity(e) and e.category.value == "component" and not e.negated
    }
    diagnosis_components = {
        e.canonical
        for e in diagnosis_ents
        if is_confirmed_entity(e) and e.category.value == "component" and not e.negated
    }
    complaint_parts = {
        e.canonical
        for e in complaint_ents
        if is_confirmed_entity(e) and e.category.value == "part" and not e.negated
    }
    diagnosis_parts = {
        e.canonical
        for e in diagnosis_ents
        if is_confirmed_entity(e) and e.category.value == "part" and not e.negated
    }
    complaint_symptoms = {
        e.canonical
        for e in complaint_ents
        if is_confirmed_entity(e) and e.category.value == "symptom" and not e.negated
    }
    diagnosis_symptoms = {
        e.canonical
        for e in diagnosis_ents
        if is_confirmed_entity(e) and e.category.value == "symptom" and not e.negated
    }

    matching = sorted(
        (complaint_components & diagnosis_components) | (complaint_parts & diagnosis_parts)
    )
    unrelated_complaint = sorted(complaint_components - diagnosis_components)
    unrelated_diagnosis = sorted(diagnosis_components - complaint_components)
    unrelated = sorted(set(unrelated_complaint + unrelated_diagnosis))
    if matching:
        unrelated = [u for u in unrelated if u not in matching]

    related_pairs: list[SymptomDiagnosisPair] = []
    for sym in complaint_symptoms:
        diag_match = sym if sym in diagnosis_symptoms else None
        note = "Symptom and diagnosis text may refer to the same issue; verify with evidence."
        if not diag_match:
            note = "Complaint lists symptoms but diagnosis does not echo them explicitly."
        related_pairs.append(
            SymptomDiagnosisPair(
                symptom_canonical=sym,
                diagnosis_canonical=diag_match,
                note=note,
            )
        )

    missing_support: list[str] = []
    notes: list[str] = []

    repair_blob = (
        claim.recommended_repair.recommended_action
        + " "
        + claim.recommended_repair.part_description
    ).lower()
    diagnosis_blob = claim.technician_diagnosis.lower()

    heavy_recommended = any(t in repair_blob for t in HEAVY_REPAIR_TERMS)
    light_diagnosis = any(t in diagnosis_blob for t in LIGHT_REPAIR_TERMS)

    if heavy_recommended and light_diagnosis:
        notes.append(
            "Recommended repair appears more extensive than the diagnosis suggests (e.g. major engine work vs timing-chain-related wording). Human verification required."
        )
        missing_support.append(
            "Supporting inspection evidence for escalation from diagnosis scope to recommended repair scope."
        )

    if unrelated:
        notes.append(
            f"Component terms differ between complaint and diagnosis: {', '.join(unrelated)}. This does not automatically invalidate the claim."
        )

    return ComplaintDiagnosisComparison(
        related_pairs=related_pairs,
        matching_components=matching,
        unrelated_components=unrelated,
        missing_diagnostic_support=missing_support,
        notes_for_reviewer=notes,
    )


def _entities(extractions: list[FieldExtraction], source: TextSourceField):
    for ext in extractions:
        if ext.source_field == source:
            return ext.entities
    return []

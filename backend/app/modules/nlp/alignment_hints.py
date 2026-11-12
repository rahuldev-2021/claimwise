"""NLP observations for repair alignment (not technical verdicts)."""

from app.modules.nlp.entity_confidence import is_confirmed_entity
from app.modules.nlp.schemas import (
    EntityCategory,
    ExtractedEntity,
    FieldExtraction,
    RepairAlignmentHint,
    RepairAlignmentHintType,
    TextSourceField,
)


def build_repair_alignment_hints(
    field_extractions: list[FieldExtraction],
    repair_entities: list[ExtractedEntity],
) -> list[RepairAlignmentHint]:
    hints: list[RepairAlignmentHint] = []

    diagnosis = _entities(field_extractions, TextSourceField.TECHNICIAN_DIAGNOSIS)
    complaint = _entities(field_extractions, TextSourceField.CUSTOMER_COMPLAINT)

    diag_components = {
        e.canonical
        for e in diagnosis
        if is_confirmed_entity(e) and e.category == EntityCategory.COMPONENT
    }
    repair_components = {
        e.canonical
        for e in repair_entities
        if is_confirmed_entity(e) and e.category == EntityCategory.COMPONENT
    }
    diag_parts = {
        e.canonical for e in diagnosis if is_confirmed_entity(e) and e.category == EntityCategory.PART
    }
    repair_parts = {
        e.canonical
        for e in repair_entities
        if is_confirmed_entity(e) and e.category == EntityCategory.PART
    }
    overlap = (diag_components & repair_components) | (diag_parts & repair_parts)
    if overlap:
        hints.append(
            RepairAlignmentHint(
                type=RepairAlignmentHintType.COMPONENT_REFERENCE_MATCH,
                description=(
                    "The recommended repair references part or component term(s) also "
                    f"mentioned in the submitted technician diagnosis field: "
                    f"{', '.join(sorted(overlap))}."
                ),
                confidence=0.9,
            )
        )

    complaint_symptoms = {
        e.canonical
        for e in complaint
        if is_confirmed_entity(e) and e.category == EntityCategory.SYMPTOM
    }
    diagnosis_symptoms = {
        e.canonical
        for e in diagnosis
        if is_confirmed_entity(e) and e.category == EntityCategory.SYMPTOM
    }
    if complaint_symptoms and not (complaint_symptoms & diagnosis_symptoms):
        hints.append(
            RepairAlignmentHint(
                type=RepairAlignmentHintType.SYMPTOM_NOT_REFLECTED_IN_DIAGNOSIS,
                description=(
                    "Complaint symptom terms are not echoed in the submitted technician "
                    "diagnosis field (reviewer may verify with supporting documents)."
                ),
                confidence=0.75,
            )
        )

    has_finding = any(
        is_confirmed_entity(e)
        and e.category in (EntityCategory.DIAGNOSTIC_FINDING, EntityCategory.MEASUREMENT, EntityCategory.DTC_CODE)
        for e in diagnosis
    )
    if not has_finding:
        hints.append(
            RepairAlignmentHint(
                type=RepairAlignmentHintType.MISSING_DIAGNOSTIC_FINDING_IN_SUBMITTED_DIAGNOSIS,
                description=(
                    "The submitted technician diagnosis field contains no extracted "
                    "diagnostic finding, measurement, or DTC code. This does not mean "
                    "evidence is absent from uploaded documents."
                ),
                confidence=0.8,
            )
        )

    dtcs = [e for e in diagnosis if is_confirmed_entity(e) and e.category == EntityCategory.DTC_CODE]
    if dtcs:
        codes = ", ".join(e.text.upper() for e in dtcs)
        hints.append(
            RepairAlignmentHint(
                type=RepairAlignmentHintType.DTC_PRESENT_IN_SUBMITTED_DIAGNOSIS,
                description=f"DTC code(s) present in submitted technician diagnosis: {codes}.",
                confidence=0.95,
            )
        )

    return hints


def _entities(field_extractions: list[FieldExtraction], source: TextSourceField) -> list[ExtractedEntity]:
    for ext in field_extractions:
        if ext.source_field == source:
            return list(ext.entities)
    return []

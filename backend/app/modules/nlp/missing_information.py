"""Detect potentially missing details for human review (not auto-rejection)."""

import re

from app.modules.nlp.schemas import FieldExtraction, MissingInformationItem, MissingInfoSeverity, TextSourceField
from app.schemas.claim import ClaimInput


def detect_missing_information(
    claim: ClaimInput,
    field_extractions: list[FieldExtraction],
) -> list[MissingInformationItem]:
    items: list[MissingInformationItem] = []

    complaint = claim.customer_complaint.lower()
    diagnosis = claim.technician_diagnosis.lower()
    repair = claim.recommended_repair.recommended_action.lower()

    if not re.search(
        r"\b(when|during|while|at|cold|hot|idle|accelerat|brak|start)\b",
        complaint,
    ):
        items.append(
            MissingInformationItem(
                code="SYMPTOM_CONTEXT",
                message="Complaint does not clearly state when or under what conditions the symptom occurs.",
                severity=MissingInfoSeverity.SUGGESTION,
            )
        )

    if len(diagnosis.strip()) < 40:
        items.append(
            MissingInformationItem(
                code="THIN_DIAGNOSIS",
                message="Technician diagnosis is brief; additional inspection findings may help review.",
                severity=MissingInfoSeverity.SUGGESTION,
            )
        )

    diag_entities = _entities_for(field_extractions, TextSourceField.TECHNICIAN_DIAGNOSIS)
    has_measurement = any(e.category.value == "measurement" for e in diag_entities)
    has_dtc = any(
        e.category.value == "dtc_code" or "p0" in e.text.lower() for e in diag_entities
    ) or "p0" in diagnosis
    if "suspect" in diagnosis and not has_measurement and not has_dtc:
        items.append(
            MissingInformationItem(
                code="MISSING_DIAGNOSTIC_EVIDENCE",
                message="Diagnosis uses tentative language but no measurements or fault codes are documented.",
                severity=MissingInfoSeverity.SUGGESTION,
            )
        )

    heavy_repair = any(
        term in repair
        for term in ("engine block", "complete engine", "valve body", "compressor assembly")
    )
    if heavy_repair and len(claim.supporting_document_ids) == 0:
        items.append(
            MissingInformationItem(
                code="NO_SUPPORTING_DOCUMENTS",
                message="Significant repair recommended but no supporting document IDs are attached.",
                severity=MissingInfoSeverity.SUGGESTION,
            )
        )

    complaint_entities = _entities_for(field_extractions, TextSourceField.CUSTOMER_COMPLAINT)
    onset_mileage = any(
        e.category.value == "measurement" and e.canonical == "symptom_onset_mileage"
        for e in complaint_entities
    )
    current_mileage_narrative = any(
        e.category.value == "measurement" and e.canonical == "mileage"
        for e in complaint_entities
    )
    if claim.vehicle.mileage is None and not onset_mileage and not current_mileage_narrative:
        items.append(
            MissingInformationItem(
                code="MISSING_MILEAGE",
                message="Vehicle mileage is not recorded on the structured claim fields.",
                severity=MissingInfoSeverity.INFO,
            )
        )
    elif claim.vehicle.mileage is None and onset_mileage:
        items.append(
            MissingInformationItem(
                code="SYMPTOM_ONSET_MILEAGE_IN_NARRATIVE",
                message=(
                    "Complaint cites mileage when the symptom reportedly started; "
                    "this is not necessarily the vehicle's current odometer reading."
                ),
                severity=MissingInfoSeverity.INFO,
            )
        )
    elif claim.vehicle.mileage is None and current_mileage_narrative:
        items.append(
            MissingInformationItem(
                code="MILEAGE_IN_NARRATIVE_ONLY",
                message=(
                    "Mileage appears in the complaint narrative but not on the structured "
                    "vehicle record; consider syncing vehicle mileage for reporting."
                ),
                severity=MissingInfoSeverity.INFO,
            )
        )

    return items


def _entities_for(
    extractions: list[FieldExtraction], source: TextSourceField
) -> list:
    for ext in extractions:
        if ext.source_field == source:
            return ext.entities
    return []

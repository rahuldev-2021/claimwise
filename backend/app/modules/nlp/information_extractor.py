"""Build per-field extractions from claim text and recommended repair."""

from app.modules.nlp.entity_extractor import extract_entities
from app.modules.nlp.preprocessing import preprocess_text
from app.modules.nlp.schemas import FieldExtraction, TextSourceField
from app.schemas.claim import ClaimInput
from app.modules.nlp.repair_text import repair_narrative_text
from app.schemas.repair import Repair


def extract_from_claim(claim: ClaimInput) -> tuple[list[FieldExtraction], list[str]]:
    """Extract structured information from complaint, diagnosis, and repair."""
    all_modes: list[str] = []

    complaint = preprocess_text(claim.customer_complaint)
    diagnosis = preprocess_text(claim.technician_diagnosis)
    repair_pp = preprocess_text(repair_narrative_text(claim.recommended_repair))

    fields: list[tuple[TextSourceField, str, str, tuple[int, ...]]] = [
        (
            TextSourceField.CUSTOMER_COMPLAINT,
            complaint.normalized,
            complaint.original,
            complaint.norm_to_orig,
        ),
        (
            TextSourceField.TECHNICIAN_DIAGNOSIS,
            diagnosis.normalized,
            diagnosis.original,
            diagnosis.norm_to_orig,
        ),
        (
            TextSourceField.RECOMMENDED_REPAIR,
            repair_pp.normalized,
            repair_pp.original,
            repair_pp.norm_to_orig,
        ),
    ]

    extractions: list[FieldExtraction] = []
    for source, text, original, norm_to_orig in fields:
        entities, modes = extract_entities(
            text,
            source,
            original=original,
            norm_to_orig=norm_to_orig,
        )
        for m in modes:
            if m not in all_modes:
                all_modes.append(m)
        phrases = _relevant_phrases(text)
        extractions.append(
            FieldExtraction(
                source_field=source,
                entities=entities,
                relevant_phrases=phrases,
            )
        )

    return extractions, all_modes


def _relevant_phrases(text: str, max_phrases: int = 5) -> list[str]:
    """Simple clause split for reviewer context."""
    if not text:
        return []
    rough = [p.strip() for p in text.replace(";", ".").split(".") if p.strip()]
    return rough[:max_phrases]

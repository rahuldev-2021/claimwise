"""NLP pipeline orchestration."""

import time
from typing import Optional

from app.modules.nlp.alignment_hints import build_repair_alignment_hints
from app.modules.nlp.entity_confidence import is_confirmed_entity
from app.modules.nlp.complaint_diagnosis_matcher import compare_complaint_and_diagnosis
from app.modules.nlp.contextual_extraction import ContextualExtractionProvider
from app.modules.nlp.entity_extractor import spacy_available
from app.modules.nlp.entity_ids import assign_entity_ids
from app.modules.nlp.information_extractor import extract_from_claim
from app.modules.nlp.missing_information import detect_missing_information
from app.modules.nlp.preprocessing import preprocess_text
from app.modules.nlp.repair_text import repair_narrative_text
from app.modules.nlp.relationship_extractor import extract_relationships
from app.modules.nlp.schemas import (
    EntityCategory,
    NLPAnalysisResult,
    ProcessingMetadata,
    RecommendedRepairExtraction,
    StructuredExtraction,
    TextSourceField,
)
from app.modules.nlp.versions import (
    PIPELINE_VERSION,
    abbreviation_dict_version,
    fuzzy_matcher_name,
)
from app.modules.nlp.taxonomy_data import TAXONOMY_VERSION
from app.schemas.claim import ClaimInput


class NLPPipeline:
    """Coordinates preprocessing through structured NLP output."""

    def __init__(
        self,
        contextual: Optional[ContextualExtractionProvider] = None,
    ) -> None:
        self._contextual = contextual

    def analyze(self, claim: ClaimInput) -> NLPAnalysisResult:
        result = self._run_deterministic(claim)
        if self._contextual is not None:
            return self._contextual.enrich(claim, result)
        return result

    def extract(self, claim: ClaimInput) -> NLPAnalysisResult:
        """Satisfies NLPModule protocol."""
        return self.analyze(claim)

    def _run_deterministic(self, claim: ClaimInput) -> NLPAnalysisResult:
        start = time.perf_counter()

        complaint_pp = preprocess_text(claim.customer_complaint)
        diagnosis_pp = preprocess_text(claim.technician_diagnosis)

        field_extractions, modes = extract_from_claim(claim)
        missing = detect_missing_information(claim, field_extractions)
        comparison = compare_complaint_and_diagnosis(claim, field_extractions)

        repair_pp = preprocess_text(repair_narrative_text(claim.recommended_repair))
        repair_entities: list = []
        for ext in field_extractions:
            if ext.source_field == TextSourceField.RECOMMENDED_REPAIR:
                repair_entities = list(ext.entities)
                break

        recommended = RecommendedRepairExtraction(
            repair_category=claim.recommended_repair.repair_category,
            part_number=claim.recommended_repair.part_number,
            part_description=claim.recommended_repair.part_description,
            recommended_action=claim.recommended_repair.recommended_action,
            entities=repair_entities,
        )

        assign_entity_ids(field_extractions)

        originals = {
            TextSourceField.CUSTOMER_COMPLAINT: complaint_pp.original,
            TextSourceField.TECHNICIAN_DIAGNOSIS: diagnosis_pp.original,
            TextSourceField.RECOMMENDED_REPAIR: repair_pp.original,
        }
        relationships = extract_relationships(field_extractions, originals=originals)
        alignment_hints = build_repair_alignment_hints(field_extractions, repair_entities)

        structured = _build_structured_extraction(claim, field_extractions, repair_entities)

        duration_ms = (time.perf_counter() - start) * 1000
        spacy_model = "en_core_web_sm" if spacy_available() else None

        return NLPAnalysisResult(
            claim_id=claim.claim_id,
            original_complaint=complaint_pp.original,
            original_diagnosis=diagnosis_pp.original,
            original_repair=repair_pp.original,
            normalized_complaint=complaint_pp.normalized,
            normalized_diagnosis=diagnosis_pp.normalized,
            normalized_repair=repair_pp.normalized,
            field_extractions=field_extractions,
            recommended_repair=recommended,
            missing_information=missing,
            complaint_diagnosis_comparison=comparison,
            repair_alignment_hints=alignment_hints,
            entity_relationships=relationships,
            structured_extraction=structured,
            processing_metadata=ProcessingMetadata(
                pipeline_version=PIPELINE_VERSION,
                duration_ms=round(duration_ms, 2),
                spacy_available=spacy_available(),
                extractor_modes=modes,
                taxonomy_version=TAXONOMY_VERSION,
                abbreviation_dict_version=abbreviation_dict_version(),
                fuzzy_matcher=fuzzy_matcher_name(),
                spacy_model=spacy_model,
            ),
        )


def _build_structured_extraction(
    claim: ClaimInput,
    field_extractions: list,
    repair_entities: list,
) -> StructuredExtraction:
    symptom = _first_canonical(
        field_extractions, TextSourceField.CUSTOMER_COMPLAINT, EntityCategory.SYMPTOM
    )
    component = _first_canonical(
        field_extractions, TextSourceField.CUSTOMER_COMPLAINT, EntityCategory.COMPONENT
    ) or _first_canonical(
        field_extractions, TextSourceField.TECHNICIAN_DIAGNOSIS, EntityCategory.COMPONENT
    )
    failure_mode = _first_canonical(
        field_extractions, TextSourceField.TECHNICIAN_DIAGNOSIS, EntityCategory.FAILURE_MODE
    )
    repair_action = _first_canonical(repair_entities, None, EntityCategory.REPAIR_ACTION)
    dtc_codes = _all_canonical(
        field_extractions, TextSourceField.TECHNICIAN_DIAGNOSIS, EntityCategory.DTC_CODE
    )
    operating = _all_canonical(
        field_extractions, TextSourceField.CUSTOMER_COMPLAINT, EntityCategory.OPERATING_CONDITION
    ) + _all_canonical(
        field_extractions, TextSourceField.TECHNICIAN_DIAGNOSIS, EntityCategory.OPERATING_CONDITION
    )
    locations = _all_canonical(
        field_extractions, TextSourceField.CUSTOMER_COMPLAINT, EntityCategory.LOCATION
    ) + _all_canonical(
        field_extractions, TextSourceField.TECHNICIAN_DIAGNOSIS, EntityCategory.LOCATION
    )
    return StructuredExtraction(
        symptom=symptom,
        component=component,
        failure_mode=failure_mode,
        repair_action=repair_action,
        part_number=claim.recommended_repair.part_number,
        dtc_codes=list(dict.fromkeys(dtc_codes)),
        operating_conditions=list(dict.fromkeys(operating)),
        locations=list(dict.fromkeys(locations)),
    )


def _first_canonical(field_extractions, source, category):
    if isinstance(field_extractions, list) and source is not None:
        for ext in field_extractions:
            if ext.source_field != source:
                continue
            for ent in ext.entities:
                if is_confirmed_entity(ent) and ent.category == category and not ent.negated:
                    return ent.canonical
    elif source is None and category:
        for ent in field_extractions:
            if is_confirmed_entity(ent) and ent.category == category and not ent.negated:
                return ent.canonical
    return None


def _all_canonical(field_extractions, source, category):
    out: list[str] = []
    for ext in field_extractions:
        if ext.source_field != source:
            continue
        for ent in ext.entities:
            if is_confirmed_entity(ent) and ent.category == category and not ent.negated:
                if category == EntityCategory.DTC_CODE:
                    out.append(ent.text.upper())
                else:
                    out.append(ent.canonical)
    return out

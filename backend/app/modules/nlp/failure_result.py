"""Minimal NLP result when the pipeline fails (claim must remain usable)."""

from app.modules.nlp.preprocessing import preprocess_text
from app.modules.nlp.repair_text import repair_narrative_text
from app.modules.nlp.schemas import (
    ComplaintDiagnosisComparison,
    NLPAnalysisResult,
    ProcessingMetadata,
    RecommendedRepairExtraction,
    StructuredExtraction,
)
from app.modules.nlp.versions import (
    PIPELINE_VERSION,
    abbreviation_dict_version,
    fuzzy_matcher_name,
)
from app.modules.nlp.taxonomy_data import TAXONOMY_VERSION
from app.schemas.claim import ClaimInput


def build_failure_result(claim: ClaimInput, error_message: str) -> NLPAnalysisResult:
    complaint_pp = preprocess_text(claim.customer_complaint)
    diagnosis_pp = preprocess_text(claim.technician_diagnosis)
    repair_pp = preprocess_text(repair_narrative_text(claim.recommended_repair))
    return NLPAnalysisResult(
        claim_id=claim.claim_id,
        original_complaint=complaint_pp.original,
        original_diagnosis=diagnosis_pp.original,
        original_repair=repair_pp.original,
        normalized_complaint=complaint_pp.normalized,
        normalized_diagnosis=diagnosis_pp.normalized,
        normalized_repair=repair_pp.normalized,
        recommended_repair=RecommendedRepairExtraction(
            repair_category=claim.recommended_repair.repair_category,
            part_number=claim.recommended_repair.part_number,
            part_description=claim.recommended_repair.part_description,
            recommended_action=claim.recommended_repair.recommended_action,
        ),
        complaint_diagnosis_comparison=ComplaintDiagnosisComparison(),
        structured_extraction=StructuredExtraction(
            part_number=claim.recommended_repair.part_number,
        ),
        processing_metadata=ProcessingMetadata(
            pipeline_version=PIPELINE_VERSION,
            taxonomy_version=TAXONOMY_VERSION,
            abbreviation_dict_version=abbreviation_dict_version(),
            fuzzy_matcher=fuzzy_matcher_name(),
        ),
        nlp_error=error_message[:2000],
    )

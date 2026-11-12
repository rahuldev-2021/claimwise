"""Minimal assessment context — only fields needed for grounded JSON output."""

import json

from app.core.config import Settings
from app.modules.nlp.schemas import NLPAnalysisResult
from app.modules.rag.schemas import RetrievalResult
from app.schemas.claim import ClaimInput
from app.schemas.technical_validation import TechnicalValidationResult


def build_compact_context_payload(
    claim: ClaimInput,
    nlp: NLPAnalysisResult,
    retrieval: RetrievalResult,
    technical: TechnicalValidationResult,
    *,
    settings: Settings | None = None,
) -> str:
    _ = (settings, retrieval)  # compact payload is claim + Phase 4 only

    payload = {
        "output_keys_only": [
            "summary",
            "suggested_alignment",
            "respects_technical_validation",
            "schema_version",
            "technical_interpretation",
        ],
        "claim_id": claim.claim_id,
        "complaint": claim.customer_complaint[:800],
        "diagnosis": claim.technician_diagnosis[:800],
        "repair_category": claim.recommended_repair.repair_category,
        "repair_action": claim.recommended_repair.recommended_action[:500],
        "technical_status": technical.technical_status.value,
        "repair_action_assessments": [
            {
                "normalized_operation": a.normalized_operation,
                "justification_status": a.justification_status.value,
                "explanation": (a.explanation or "")[:200],
            }
            for a in technical.repair_action_assessments
        ],
        "nlp_note": (nlp.complaint_diagnosis_comparison.matching_components or [])[:5],
    }
    return json.dumps(payload, ensure_ascii=False)

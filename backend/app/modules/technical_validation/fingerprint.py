"""Input fingerprint for idempotent technical validation."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from app.modules.nlp.schemas import NLPAnalysisResult
from app.modules.rag.schemas import RetrievalResult
from app.modules.technical_validation.versions import TV_PIPELINE_VERSION, TV_RULES_VERSION
from app.schemas.claim import ClaimInput


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, default=str)


def build_input_fingerprint(
    claim: ClaimInput,
    nlp: NLPAnalysisResult,
    retrieval: RetrievalResult,
    *,
    top_k: int,
) -> str:
    claim_part = {
        "claim_id": claim.claim_id,
        "complaint": claim.customer_complaint,
        "diagnosis": claim.technician_diagnosis,
        "repair_category": claim.recommended_repair.repair_category,
        "recommended_action": claim.recommended_repair.recommended_action,
        "part_description": claim.recommended_repair.part_description,
        "vin": claim.vehicle.vin,
        "make": claim.vehicle.make,
        "model": claim.vehicle.model,
        "year": claim.vehicle.model_year,
        "supporting_document_ids": sorted(claim.supporting_document_ids),
    }
    nlp_part = {
        "pipeline_version": nlp.processing_metadata.pipeline_version,
        "comparison": nlp.complaint_diagnosis_comparison.model_dump(mode="json"),
        "structured": nlp.structured_extraction.model_dump(mode="json"),
    }
    retrieval_part = {
        "chunk_ids": sorted(p.chunk_id for p in retrieval.passages),
        "strategy": retrieval.strategy.value,
        "embedding_model": retrieval.embedding_model,
        "top_k": top_k,
    }
    meta = {
        "tv_pipeline": TV_PIPELINE_VERSION,
        "tv_rules": TV_RULES_VERSION,
        "claim": claim_part,
        "nlp": nlp_part,
        "retrieval": retrieval_part,
    }
    digest = hashlib.sha256(_stable_json(meta).encode("utf-8")).hexdigest()
    return digest

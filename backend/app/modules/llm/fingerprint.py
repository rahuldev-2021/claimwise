"""Phase 5 input fingerprint for idempotent LLM recommendation reuse."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from app.core.config import Settings
from app.modules.llm.versions import DEFAULT_PROMPT_VERSION, LLM_SCHEMA_VERSION
from app.modules.nlp.schemas import NLPAnalysisResult
from app.modules.rag.schemas import RetrievalResult
from app.schemas.claim import ClaimInput
from app.schemas.technical_validation import TechnicalValidationResult


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, default=str)


def build_phase5_input_fingerprint(
    claim: ClaimInput,
    nlp: NLPAnalysisResult,
    retrieval: RetrievalResult,
    technical: TechnicalValidationResult,
    *,
    settings: Settings,
    top_k: int,
    prompt_version: str,
    schema_version: str,
    provider: str,
    model: str,
) -> str:
    meta = {
        "phase5_schema": schema_version,
        "prompt_version": prompt_version,
        "llm_provider": provider,
        "llm_model": model,
        "tv_input_fingerprint": technical.input_fingerprint,
        "tv_validation_id": technical.validation_id,
        "rag_chunk_ids": sorted(p.chunk_id for p in retrieval.passages),
        "rag_strategy": retrieval.strategy.value,
        "rag_embedding_model": retrieval.embedding_model,
        "top_k": top_k,
        "claim_id": claim.claim_id,
        "nlp_pipeline": nlp.processing_metadata.pipeline_version,
        "llm_context_max_chars": settings.LLM_CONTEXT_MAX_CHARS,
        "llm_context_max_passages": settings.LLM_CONTEXT_MAX_PASSAGES,
    }
    digest = hashlib.sha256(_stable_json(meta).encode("utf-8")).hexdigest()
    return digest


def default_prompt_version(settings: Settings) -> str:
    v = (settings.LLM_PROMPT_VERSION or "").strip()
    return v or DEFAULT_PROMPT_VERSION

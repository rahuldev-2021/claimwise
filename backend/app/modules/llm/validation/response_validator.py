"""Validate LLM structured output against schema and evidence grounding."""

import re

from pydantic import ValidationError

from app.modules.llm.compliance import verify_respects_technical_validation
from app.modules.llm.schemas.llm_assessment import LLMAssessmentResponse
from app.modules.llm.validation.enrich_from_tv import enrich_llm_payload_from_tv
from app.modules.llm.validation.minimal_payload import coerce_minimal_llm_payload
from app.modules.rag.schemas import RetrievalResult
from app.schemas.technical_validation import TechnicalValidationResult


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


class EvidenceCatalog:
    def __init__(self, retrieval: RetrievalResult, technical: TechnicalValidationResult) -> None:
        self._by_doc: dict[str, list[str]] = {}
        self._by_chunk: dict[str, str] = {}
        for passage in retrieval.passages:
            self._by_doc.setdefault(passage.document_id, []).append(passage.text)
            self._by_chunk[passage.chunk_id] = passage.text
        all_items = (
            technical.supporting_evidence
            + technical.contradictory_evidence
            + technical.contextual_evidence
        )
        for item in all_items:
            if item.chunk_id:
                self._by_chunk.setdefault(item.chunk_id, item.relevant_excerpt)
            self._by_doc.setdefault(item.document_id, []).append(item.relevant_excerpt)

    @property
    def document_ids(self) -> set[str]:
        return set(self._by_doc.keys())

    @property
    def chunk_ids(self) -> set[str]:
        return set(self._by_chunk.keys())

    def excerpt_is_grounded(self, document_id: str, chunk_id: str | None, excerpt: str) -> bool:
        if not excerpt.strip():
            return True
        norm_excerpt = _normalize_ws(excerpt)
        if chunk_id and chunk_id in self._by_chunk:
            return norm_excerpt in _normalize_ws(self._by_chunk[chunk_id])
        for text in self._by_doc.get(document_id, []):
            if norm_excerpt in _normalize_ws(text):
                return True
        return False


def validate_assessment_response(
    data: dict,
    *,
    catalog: EvidenceCatalog,
    technical: TechnicalValidationResult,
) -> tuple[LLMAssessmentResponse | None, list[str]]:
    errors: list[str] = []
    try:
        data = coerce_minimal_llm_payload(data)
        if not (data.get("summary") or "").strip():
            return None, ["summary is required and must be non-empty"]
        data = enrich_llm_payload_from_tv(data, technical)
        parsed = LLMAssessmentResponse.model_validate(data)
    except ValidationError as exc:
        return None, [str(exc)]

    if not parsed.respects_technical_validation:
        errors.append("LLM must respect technical validation (respects_technical_validation=false)")

    errors.extend(verify_respects_technical_validation(parsed, technical))

    for cite in parsed.cited_evidence:
        if cite.document_id not in catalog.document_ids:
            errors.append(f"Unknown document_id in citation: {cite.document_id}")
        if cite.chunk_id and cite.chunk_id not in catalog.chunk_ids:
            errors.append(f"Unknown chunk_id in citation: {cite.chunk_id}")
        if cite.excerpt and not catalog.excerpt_is_grounded(
            cite.document_id, cite.chunk_id, cite.excerpt
        ):
            errors.append(f"Ungrounded excerpt for {cite.document_id}")

    if technical.repair_action_assessments:
        tv_ops = {a.normalized_operation for a in technical.repair_action_assessments}
        llm_ops = {i.normalized_operation for i in parsed.repair_interpretations}
        missing = tv_ops - llm_ops
        if missing:
            errors.append(f"repair_interpretations missing operations: {sorted(missing)}")
        extra = llm_ops - tv_ops
        if extra:
            errors.append(f"repair_interpretations unknown operations: {sorted(extra)}")

    if parsed.technical_interpretation is None:
        errors.append("technical_interpretation is required for schema v2")
    elif parsed.technical_interpretation.advisory_status != technical.technical_status.value:
        errors.append("technical_interpretation.advisory_status must match technical_status")

    if errors:
        return None, errors
    return parsed, []

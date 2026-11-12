"""Conditional LLM enrichment via ContextualExtractionProvider."""

from __future__ import annotations

import logging
import re

from app.core.config import Settings
from app.modules.llm.interfaces.llm_schemas import LLMRequest
from app.modules.nlp.fallback_decision import evaluate_fallback
from app.modules.nlp.llm_context_builder import build_nlp_llm_context
from app.modules.nlp.llm_nlp_prompt import NLP_FALLBACK_SYSTEM, PROMPT_VERSION, build_user_prompt
from app.modules.nlp.llm_nlp_reconcile import reconcile_llm_extraction
from app.modules.llm.validation.response_parser import extract_json_text
from app.modules.nlp.llm_nlp_schemas import LLMNlpExtractionResponse
from app.modules.nlp.llm_nlp_validator import validate_llm_nlp_response
from app.modules.nlp.nlp_llm_provider import create_nlp_llm_provider
from app.modules.nlp.schemas import (
    LLMFallbackExecution,
    LLMFallbackMetadata,
    NLPAnalysisResult,
    TextSourceField,
)
from app.schemas.claim import ClaimInput

logger = logging.getLogger(__name__)


class LLMContextualExtractionProvider:
    """Optional LLM fallback; never blocks deterministic output."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def enrich(self, claim: ClaimInput, deterministic: NLPAnalysisResult) -> NLPAnalysisResult:
        decision = evaluate_fallback(claim, deterministic, self._settings)
        meta = LLMFallbackMetadata(
            enabled=self._settings.LLM_NLP_ENABLED,
            mode=self._settings.LLM_NLP_FALLBACK_MODE,
            decision=decision,
        )
        out = self._attach_meta(deterministic, meta)
        claim_id = claim.claim_id
        provider_name = (self._settings.LLM_NLP_PROVIDER or self._settings.LLM_PROVIDER or "").strip()
        model_name = (self._settings.LLM_NLP_MODEL or self._settings.LLM_MODEL or "").strip()

        logger.info(
            "NLP LLM fallback decision for %s: enabled=%s mode=%s triggered=%s codes=%s",
            claim_id,
            self._settings.LLM_NLP_ENABLED,
            self._settings.LLM_NLP_FALLBACK_MODE,
            decision.triggered,
            ",".join(decision.trigger_codes) or "none",
        )

        if not self._settings.LLM_NLP_ENABLED:
            logger.info("NLP LLM fallback skipped for %s: reason=disabled", claim_id)
            return out
        if not decision.triggered:
            logger.info(
                "NLP LLM fallback skipped for %s: reason=threshold_not_met (need %s triggers)",
                claim_id,
                self._settings.LLM_NLP_MIN_TRIGGER_COUNT,
            )
            return out

        decision.invoked = True
        logger.info(
            "NLP LLM fallback invoking for %s: provider=%s model=%s",
            claim_id,
            provider_name or "default",
            model_name or "default",
        )
        originals = {
            TextSourceField.CUSTOMER_COMPLAINT: out.original_complaint,
            TextSourceField.TECHNICIAN_DIAGNOSIS: out.original_diagnosis,
            TextSourceField.RECOMMENDED_REPAIR: out.original_repair,
        }
        context_json = build_nlp_llm_context(claim, out)
        request = LLMRequest(
            system_instruction=NLP_FALLBACK_SYSTEM,
            user_prompt=build_user_prompt(context_json),
            temperature=self._settings.LLM_TEMPERATURE,
            max_output_tokens=self._settings.LLM_NLP_MAX_OUTPUT_TOKENS,
            timeout_seconds=self._settings.LLM_NLP_TIMEOUT_SECONDS,
            prompt_version=PROMPT_VERSION,
        )

        last_error: str | None = None
        last_finish_reason: str | None = None
        last_output_tokens: int | None = None
        retries = max(0, self._settings.LLM_NLP_MAX_RETRIES)
        for attempt in range(retries + 1):
            try:
                provider = create_nlp_llm_provider(self._settings)
                response = provider.generate_sync(request)
                last_finish_reason = response.finish_reason
                last_output_tokens = response.output_tokens
                raw = extract_json_text(_strip_json_fence(response.raw_text))
                parsed, errors = validate_llm_nlp_response(raw, originals=originals)
                if parsed is None:
                    last_error = "; ".join(errors[:5])
                    if response.finish_reason == "length":
                        last_error = f"truncated_output({last_error})"
                    err_summary = last_error
                    if err_summary.startswith("schema:"):
                        err_summary = err_summary.split("\n", 1)[0][:240]
                    logger.warning(
                        "NLP LLM fallback validation failed for %s (attempt %s): %s",
                        claim_id,
                        attempt + 1,
                        err_summary,
                    )
                    if errors and errors[0].startswith("invalid_json"):
                        tail = raw[-200:].replace("\n", "\\n")
                        logger.warning(
                            "NLP LLM fallback invalid JSON for %s: bytes=%s finish_reason=%s "
                            "output_tokens=%s tail=%r",
                            claim_id,
                            len(raw),
                            response.finish_reason,
                            response.output_tokens,
                            tail,
                        )
                    continue
                if not _llm_payload_usable(
                    parsed, raw=raw, finish_reason=response.finish_reason
                ):
                    last_error = "empty_or_truncated_response"
                    logger.warning(
                        "NLP LLM fallback unusable response for %s (attempt %s): "
                        "finish_reason=%s bytes=%s entities=%s",
                        claim_id,
                        attempt + 1,
                        response.finish_reason,
                        len(raw),
                        len(parsed.entities),
                    )
                    continue
                before = _count_entities(out)
                merged, conflicts = reconcile_llm_extraction(out, parsed)
                added = _count_entities(merged) - before
                added_rels = len(parsed.relationships)
                decision.succeeded = True
                meta.reconciliation_conflict_count = len(conflicts)
                meta.conflicts = conflicts
                meta.execution = LLMFallbackExecution(
                    provider=response.provider,
                    model=response.model,
                    latency_ms=response.latency_ms,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    finish_reason=response.finish_reason,
                    response_bytes=len(raw),
                )
                logger.info(
                    "NLP LLM fallback succeeded for %s: provider=%s model=%s latency_ms=%s "
                    "llm_entities_added=%s llm_relationships=%s conflicts=%s finish_reason=%s",
                    claim_id,
                    response.provider,
                    response.model,
                    round(response.latency_ms, 2),
                    added,
                    added_rels,
                    len(conflicts),
                    response.finish_reason,
                )
                return self._attach_meta(merged, meta)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "NLP LLM fallback attempt %s failed for %s: %s",
                    attempt + 1,
                    claim_id,
                    exc,
                )
                last_error = type(exc).__name__

        decision.succeeded = False
        meta.execution = LLMFallbackExecution(
            provider=provider_name or None,
            model=model_name or None,
            output_tokens=last_output_tokens,
            error_code=last_error or "llm_failed",
        )
        logger.warning(
            "NLP LLM fallback failed for %s: error=%s (deterministic output kept)",
            claim_id,
            last_error or "llm_failed",
        )
        return self._attach_meta(out, meta)

    def _attach_meta(
        self, result: NLPAnalysisResult, meta: LLMFallbackMetadata
    ) -> NLPAnalysisResult:
        pmd = result.processing_metadata.model_copy(update={"llm_fallback": meta})
        return result.model_copy(update={"processing_metadata": pmd})


def _count_entities(result: NLPAnalysisResult) -> int:
    return sum(len(ext.entities) for ext in result.field_extractions)


def _llm_payload_usable(
    parsed: LLMNlpExtractionResponse,
    *,
    raw: str,
    finish_reason: str | None,
) -> bool:
    has_items = bool(parsed.entities or parsed.relationships or parsed.observations)
    if finish_reason == "length" and not has_items:
        return False
    if len(raw.strip()) <= 4 and not has_items:
        return False
    return True


def _strip_json_fence(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text

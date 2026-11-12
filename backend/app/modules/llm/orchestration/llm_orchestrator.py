"""Coordinates provider calls, parsing, and validation."""

import asyncio
import logging

from app.core.config import Settings
from app.modules.llm.context.compact_context import build_compact_context_payload
from app.modules.llm.context.contextual_input_builder import build_context_payload
from app.modules.llm.exceptions import LLMCapabilityError
from app.modules.llm.factory.provider_factory import ProviderFactory
from app.modules.llm.interfaces.base_provider import BaseLLMProvider
from app.modules.llm.interfaces.llm_schemas import LLMRequest, LLMResponse
from app.modules.llm.orchestration.fallback_manager import FallbackManager
from app.modules.llm.prompt_management.prompt_manager import PromptManager
from app.modules.llm.schemas.llm_assessment import LLMContextualAssessment
from app.modules.llm.validation.enrich_from_tv import build_template_assessment_from_tv
from app.modules.llm.validation.json_repair import REPAIR_SYSTEM, build_json_repair_prompt
from app.modules.llm.versions import LLM_SCHEMA_VERSION
from app.modules.llm.validation.narrative_brevity import clamp_assessment_narrative
from app.modules.llm.validation.response_parser import parse_json_dict
from app.modules.llm.validation.response_validator import EvidenceCatalog, validate_assessment_response
from app.modules.nlp.schemas import NLPAnalysisResult
from app.modules.rag.schemas import RetrievalResult
from app.schemas.claim import ClaimInput
from app.schemas.llm_execution import LLMExecutionRecord, LLMExecutionStatus
from app.schemas.technical_validation import TechnicalValidationResult

logger = logging.getLogger(__name__)


def _validate_response(
    response: LLMResponse,
    *,
    catalog: EvidenceCatalog,
    technical: TechnicalValidationResult,
) -> tuple[object | None, list[str]]:
    validation_errors: list[str] = []
    try:
        data = parse_json_dict(response.raw_text)
    except ValueError as exc:
        return None, [str(exc)]
    if not data or not str(data.get("summary") or "").strip():
        return None, ["LLM returned empty or invalid JSON (missing summary)"]
    parsed, val_errors = validate_assessment_response(data, catalog=catalog, technical=technical)
    validation_errors.extend(val_errors)
    return parsed, validation_errors


def _preview_raw(text: str, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


class LLMOrchestrator:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._prompts = PromptManager(settings)
        self._fallback = FallbackManager(settings)

    def _build_context(
        self,
        claim: ClaimInput,
        nlp: NLPAnalysisResult,
        retrieval: RetrievalResult,
        technical: TechnicalValidationResult,
    ) -> str:
        if self._settings.LLM_COMPACT_CONTEXT:
            return build_compact_context_payload(claim, nlp, retrieval, technical, settings=self._settings)
        return build_context_payload(claim, nlp, retrieval, technical, settings=self._settings)

    async def _call_provider(
        self,
        provider: BaseLLMProvider,
        request: LLMRequest,
    ) -> tuple[LLMResponse | None, str, str, list[str]]:
        return await self._fallback.execute(request, provider)

    def run_contextual_assessment(
        self,
        claim: ClaimInput,
        nlp: NLPAnalysisResult,
        retrieval: RetrievalResult,
        technical: TechnicalValidationResult,
        *,
        provider: str | None = None,
    ) -> tuple[LLMContextualAssessment | None, LLMExecutionRecord]:
        if not self._settings.LLM_ENABLED:
            return None, LLMExecutionRecord(
                status=LLMExecutionStatus.DISABLED,
                configured_provider=self._settings.LLM_PROVIDER,
            )

        try:
            llm_provider = ProviderFactory.create(self._settings, provider_name=provider)
        except Exception as exc:
            logger.warning("LLM provider configuration error: %s", exc)
            return None, LLMExecutionRecord(
                status=LLMExecutionStatus.FAILED,
                configured_provider=self._settings.LLM_PROVIDER,
                error_message=str(exc),
            )

        if not llm_provider.capabilities().supports_structured_output():
            raise LLMCapabilityError(
                f"Provider {llm_provider.provider_id} does not support structured JSON output"
            )

        context_json = self._build_context(claim, nlp, retrieval, technical)
        base_user_prompt = self._prompts.user_prompt(context_json)
        request = LLMRequest(
            system_instruction=self._prompts.system_instruction(),
            user_prompt=base_user_prompt,
            temperature=self._settings.LLM_TEMPERATURE,
            max_output_tokens=self._settings.LLM_MAX_OUTPUT_TOKENS,
            timeout_seconds=self._settings.LLM_TIMEOUT_SECONDS,
            prompt_version=self._prompts.version,
        )

        catalog = EvidenceCatalog(retrieval, technical)
        max_regen = max(0, self._settings.LLM_MAX_RETRIES)
        validation_errors: list[str] = []
        parsed = None
        response: LLMResponse | None = None
        used_provider = llm_provider.provider_id
        used_model = llm_provider.model_name
        attempts: list[str] = []
        json_repair_attempted = False
        last_raw = ""
        log_chars = max(500, self._settings.LLM_RAW_OUTPUT_LOG_CHARS)
        preview_chars = max(500, self._settings.LLM_RAW_OUTPUT_PREVIEW_CHARS)

        for regen in range(max_regen + 1):
            if regen > 0:
                err_block = "\n".join(f"- {e}" for e in validation_errors[-8:])
                request = LLMRequest(
                    system_instruction=self._prompts.system_instruction(),
                    user_prompt=(
                        f"{base_user_prompt}\n\n"
                        "Previous JSON failed. Return corrected JSON only.\n"
                        f"Errors:\n{err_block}\n"
                    ),
                    temperature=min(self._settings.LLM_TEMPERATURE, 0.1),
                    max_output_tokens=self._settings.LLM_MAX_OUTPUT_TOKENS,
                    timeout_seconds=self._settings.LLM_TIMEOUT_SECONDS,
                    prompt_version=self._prompts.version,
                )

            response, used_provider, used_model, attempt_notes = asyncio.run(
                self._call_provider(llm_provider, request)
            )
            attempts.extend(attempt_notes)
            if response is None:
                break

            last_raw = response.raw_text or ""
            logger.info(
                "LLM assessment raw output claim=%s len=%s preview=%s",
                claim.claim_id,
                len(last_raw),
                _preview_raw(last_raw, log_chars),
            )

            parsed, val_errors = _validate_response(
                response, catalog=catalog, technical=technical
            )
            validation_errors.extend(val_errors)
            if parsed is not None:
                break

        if (
            parsed is None
            and response is not None
            and self._settings.LLM_JSON_REPAIR_ENABLED
            and last_raw.strip()
            and last_raw.strip() != "{}"
        ):
            json_repair_attempted = True
            attempts.append("json_repair:minimal_prompt")
            repair_user = build_json_repair_prompt(last_raw, validation_errors, technical)
            repair_request = LLMRequest(
                system_instruction=REPAIR_SYSTEM,
                user_prompt=repair_user,
                temperature=0.0,
                max_output_tokens=self._settings.LLM_MAX_OUTPUT_TOKENS,
                timeout_seconds=self._settings.LLM_TIMEOUT_SECONDS,
                prompt_version=f"{self._prompts.version}+json_repair",
            )
            repair_resp, used_provider, used_model, repair_notes = asyncio.run(
                self._call_provider(llm_provider, repair_request)
            )
            attempts.extend(repair_notes)
            if repair_resp is not None:
                logger.info(
                    "LLM json_repair output claim=%s len=%s preview=%s",
                    claim.claim_id,
                    len(repair_resp.raw_text or ""),
                    _preview_raw(repair_resp.raw_text or "", log_chars),
                )
                parsed, val_errors = _validate_response(
                    repair_resp, catalog=catalog, technical=technical
                )
                validation_errors.extend(val_errors)
                if parsed is not None:
                    response = repair_resp
                    last_raw = repair_resp.raw_text or last_raw

        fallback_name = (self._settings.LLM_FALLBACK_PROVIDER or "").strip().lower()
        if parsed is None and fallback_name == "mock" and llm_provider.provider_id != "mock":
            try:
                mock_provider = ProviderFactory.create(self._settings, provider_name="mock")
                mock_response, used_provider, used_model, mock_attempts = asyncio.run(
                    self._call_provider(mock_provider, request)
                )
                attempts.extend(mock_attempts)
                attempts.append("validation_fallback:mock")
                if mock_response is not None:
                    parsed, val_errors = _validate_response(
                        mock_response, catalog=catalog, technical=technical
                    )
                    validation_errors.extend(val_errors)
                    if parsed is not None:
                        response = mock_response
                        last_raw = mock_response.raw_text or last_raw
            except Exception as exc:
                attempts.append("mock_fallback_error:" + str(exc))

        if parsed is None and self._settings.LLM_TV_TEMPLATE_FALLBACK:
            parsed = build_template_assessment_from_tv(technical)
            used_provider = used_provider or llm_provider.provider_id
            used_model = used_model or llm_provider.model_name
            attempts.append("advisory_fallback:technical_validation_template")
            validation_errors = []

        raw_preview = _preview_raw(last_raw, preview_chars) if last_raw else None

        if response is None and parsed is None:
            return None, LLMExecutionRecord(
                status=LLMExecutionStatus.FAILED,
                configured_provider=self._settings.LLM_PROVIDER,
                actual_provider=used_provider,
                actual_model=used_model,
                prompt_version=self._prompts.version,
                attempt_notes=attempts,
                validation_errors=[],
                raw_output_preview=None,
                json_repair_attempted=json_repair_attempted,
                error_message="All LLM attempts failed",
            )

        if parsed is None:
            return None, LLMExecutionRecord(
                status=LLMExecutionStatus.FAILED,
                configured_provider=self._settings.LLM_PROVIDER,
                actual_provider=used_provider,
                actual_model=used_model,
                prompt_version=self._prompts.version,
                input_tokens=response.input_tokens if response else None,
                output_tokens=response.output_tokens if response else None,
                latency_ms=response.latency_ms if response else None,
                attempt_notes=attempts,
                validation_errors=[],
                raw_output_preview=None,
                json_repair_attempted=json_repair_attempted,
                error_message="LLM output failed validation",
            )

        status = LLMExecutionStatus.SUCCESS
        if used_provider != llm_provider.provider_id:
            status = LLMExecutionStatus.FALLBACK
        if "advisory_fallback:technical_validation_template" in attempts:
            status = LLMExecutionStatus.FALLBACK

        parsed = clamp_assessment_narrative(parsed)

        assessment = LLMContextualAssessment(
            assessment=parsed,
            prompt_version=self._prompts.version,
            schema_version=LLM_SCHEMA_VERSION,
        )
        execution = LLMExecutionRecord(
            status=status,
            configured_provider=self._settings.LLM_PROVIDER,
            actual_provider=used_provider,
            actual_model=used_model,
            prompt_version=self._prompts.version,
            input_tokens=response.input_tokens if response else None,
            output_tokens=response.output_tokens if response else None,
            latency_ms=response.latency_ms if response else None,
            attempt_notes=attempts,
            validation_errors=[],
            raw_output_preview=None,
            json_repair_attempted=json_repair_attempted,
        )
        return assessment, execution

"""Deterministic mock provider for tests."""

import json
import re
import time

from app.modules.llm.configuration.capabilities import ProviderCapabilities
from app.modules.llm.interfaces.base_provider import BaseLLMProvider
from app.modules.llm.interfaces.llm_schemas import LLMRequest, LLMResponse
from app.modules.llm.schemas.llm_assessment import TechnicalAlignment, TechnicalInterpretation


class MockLLMProvider(BaseLLMProvider):
    def __init__(self, model: str = "mock-model", response_json: str | None = None) -> None:
        self._model = model
        self._response_json = response_json

    @property
    def provider_id(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return self._model

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(structured_json=True, json_schema=True)

    def _context_from_request(self, request: LLMRequest) -> dict | None:
        match = re.search(r"\{[\s\S]*\}\s*\Z", request.user_prompt)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    def _default_payload(self, request: LLMRequest | None = None) -> dict:
        tv_status = "QUESTIONABLE"
        if request:
            ctx = self._context_from_request(request)
            if ctx:
                tv = ctx.get("technical_validation_authoritative") or {}
                tv_status = tv.get("technical_status") or ctx.get("technical_status") or tv_status

        return {
            "summary": "Mock contextual summary for testing.",
            "suggested_alignment": TechnicalAlignment.PARTIALLY_ALIGNED.value,
            "respects_technical_validation": True,
            "schema_version": "assessment_schema_v2",
            "technical_interpretation": TechnicalInterpretation(
                advisory_status=tv_status,
                explanation="Mock echo of Phase 4 technical status.",
            ).model_dump(),
        }

    async def generate(self, request: LLMRequest) -> LLMResponse:
        started = time.perf_counter()
        if self._response_json:
            text = self._response_json
        else:
            text = json.dumps(self._default_payload(request))
        latency = (time.perf_counter() - started) * 1000
        return LLMResponse(
            raw_text=text,
            provider=self.provider_id,
            model=self._model,
            prompt_version=request.prompt_version,
            input_tokens=100,
            output_tokens=200,
            latency_ms=latency,
            success=True,
        )

    async def health_check(self) -> bool:
        return True

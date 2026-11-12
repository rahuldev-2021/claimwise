"""Ollama HTTP adapter."""

import time

import httpx

from app.core.config import Settings
from app.modules.llm.configuration.capabilities import ProviderCapabilities
from app.modules.llm.exceptions import LLMConfigurationError, LLMProviderError
from app.modules.llm.interfaces.base_provider import BaseLLMProvider
from app.modules.llm.interfaces.llm_schemas import LLMRequest, LLMResponse


class OllamaProvider(BaseLLMProvider):
    def __init__(self, settings: Settings) -> None:
        model = (settings.LLM_MODEL or "").strip()
        if not model:
            raise LLMConfigurationError("LLM_MODEL is required when LLM_PROVIDER=ollama")
        self._base_url = (settings.OLLAMA_BASE_URL or "http://localhost:11434").rstrip("/")
        self._model = model
        self._timeout = settings.LLM_TIMEOUT_SECONDS

    @property
    def provider_id(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(structured_json=True, streaming=True)

    async def generate(self, request: LLMRequest) -> LLMResponse:
        started = time.perf_counter()
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": request.system_instruction},
                {"role": "user", "content": request.user_prompt},
            ],
            "stream": False,
            "options": {"temperature": request.temperature},
        }
        url = f"{self._base_url}/api/chat"
        try:
            async with httpx.AsyncClient(timeout=request.timeout_seconds) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise LLMProviderError(
                f"Ollama request failed: {exc}",
                provider=self.provider_id,
                retryable=True,
            ) from exc

        message = data.get("message", {})
        raw = message.get("content", "") if isinstance(message, dict) else ""
        latency = (time.perf_counter() - started) * 1000
        return LLMResponse(
            raw_text=raw,
            provider=self.provider_id,
            model=self._model,
            prompt_version=request.prompt_version,
            latency_ms=latency,
            success=True,
        )

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self._base_url}/api/tags")
                return r.status_code == 200
        except httpx.HTTPError:
            return False

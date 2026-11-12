"""Anthropic Claude adapter."""

import asyncio
import time

from app.core.config import Settings
from app.modules.llm.configuration.capabilities import ProviderCapabilities
from app.modules.llm.exceptions import LLMConfigurationError, LLMProviderError
from app.modules.llm.interfaces.base_provider import BaseLLMProvider
from app.modules.llm.interfaces.llm_schemas import LLMRequest, LLMResponse


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, settings: Settings) -> None:
        api_key = (settings.ANTHROPIC_API_KEY or "").strip()
        if not api_key:
            raise LLMConfigurationError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        model = (settings.LLM_MODEL or "").strip()
        if not model:
            raise LLMConfigurationError("LLM_MODEL is required when LLM_PROVIDER=anthropic")
        self._api_key = api_key
        self._model = model

    @property
    def provider_id(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return self._model

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(structured_json=True, tool_calling=True, streaming=True)

    async def generate(self, request: LLMRequest) -> LLMResponse:
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise LLMConfigurationError(
                'anthropic SDK not installed. Use: pip install -e ".[llm-anthropic]"'
            ) from exc

        started = time.perf_counter()
        client = Anthropic(api_key=self._api_key)

        def _call() -> str:
            message = client.messages.create(
                model=self._model,
                max_tokens=request.max_output_tokens,
                temperature=request.temperature,
                system=request.system_instruction,
                messages=[{"role": "user", "content": request.user_prompt}],
                timeout=request.timeout_seconds,
            )
            parts = []
            for block in message.content:
                if getattr(block, "type", None) == "text":
                    parts.append(block.text)
            return "".join(parts) or "{}"

        try:
            raw = await asyncio.to_thread(_call)
        except Exception as exc:
            raise LLMProviderError(
                f"Anthropic request failed: {exc}",
                provider=self.provider_id,
                retryable=True,
            ) from exc

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
            from anthropic import Anthropic
        except ImportError:
            return False
        try:
            client = Anthropic(api_key=self._api_key)
            await asyncio.to_thread(
                lambda: client.messages.create(
                    model=self._model,
                    max_tokens=8,
                    messages=[{"role": "user", "content": "ping"}],
                )
            )
            return True
        except Exception:
            return False

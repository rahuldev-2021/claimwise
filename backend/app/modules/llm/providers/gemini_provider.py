"""Google Gemini adapter."""

import asyncio
import json
import time

from app.core.config import Settings
from app.modules.llm.configuration.capabilities import ProviderCapabilities
from app.modules.llm.exceptions import LLMConfigurationError, LLMProviderError
from app.modules.llm.interfaces.base_provider import BaseLLMProvider
from app.modules.llm.interfaces.llm_schemas import LLMRequest, LLMResponse


class GeminiProvider(BaseLLMProvider):
    def __init__(self, settings: Settings) -> None:
        api_key = (settings.GEMINI_API_KEY or "").strip()
        if not api_key:
            raise LLMConfigurationError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        self._api_key = api_key
        self._model = settings.LLM_MODEL or "gemini-2.0-flash"
        self._timeout = settings.LLM_TIMEOUT_SECONDS

    @property
    def provider_id(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            structured_json=True,
            json_schema=True,
            streaming=True,
            max_context_tokens=1_000_000,
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        try:
            from google import genai
        except ImportError as exc:
            raise LLMConfigurationError(
                "google-genai is not installed. Use: pip install -e \".[llm-gemini]\""
            ) from exc

        started = time.perf_counter()
        client = genai.Client(api_key=self._api_key)

        def _call() -> str:
            config = genai.types.GenerateContentConfig(
                temperature=request.temperature,
                max_output_tokens=request.max_output_tokens,
                response_mime_type="application/json",
            )
            response = client.models.generate_content(
                model=self._model,
                contents=[
                    genai.types.Content(
                        role="user",
                        parts=[
                            genai.types.Part(text=request.system_instruction + "\n\n" + request.user_prompt),
                        ],
                    )
                ],
                config=config,
            )
            return response.text or "{}"

        try:
            raw = await asyncio.wait_for(
                asyncio.to_thread(_call),
                timeout=request.timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            raise LLMProviderError(
                "Gemini request timed out",
                provider=self.provider_id,
                retryable=True,
            ) from exc
        except Exception as exc:
            raise LLMProviderError(
                f"Gemini request failed: {exc}",
                provider=self.provider_id,
                retryable=True,
            ) from exc

        latency = (time.perf_counter() - started) * 1000
        # Validate JSON shape early; orchestrator will re-validate against schema
        if raw.strip():
            try:
                json.loads(raw)
            except json.JSONDecodeError as exc:
                raise LLMProviderError(
                    "Gemini returned non-JSON content",
                    provider=self.provider_id,
                    retryable=True,
                ) from exc

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
            from google import genai
        except ImportError:
            return False
        try:
            client = genai.Client(api_key=self._api_key)
            await asyncio.to_thread(
                lambda: client.models.generate_content(
                    model=self._model,
                    contents="ping",
                )
            )
            return True
        except Exception:
            return False

"""LiteLLM adapter — same message contract as OpenAIProvider."""

import asyncio
import logging
import time

from app.core.config import Settings
from app.modules.llm.configuration.capabilities import ProviderCapabilities
from app.modules.llm.exceptions import LLMConfigurationError, LLMProviderError
from app.modules.llm.interfaces.base_provider import BaseLLMProvider
from app.modules.llm.interfaces.llm_schemas import LLMRequest, LLMResponse
from app.modules.llm.litellm_runtime import bootstrap_llm_environment, resolve_model

logger = logging.getLogger(__name__)


class LiteLLMProvider(BaseLLMProvider):
    def __init__(self, settings: Settings) -> None:
        bootstrap_llm_environment(settings)
        api_key = (settings.OPENAI_API_KEY or "").strip()
        if not api_key:
            raise LLMConfigurationError(
                "OPENAI_API_KEY (or gateway key) is required when LLM_PROVIDER=litellm"
            )
        model = (settings.LLM_MODEL or "").strip()
        if not model:
            raise LLMConfigurationError("LLM_MODEL is required when LLM_PROVIDER=litellm")
        self._settings = settings
        self._configured_model = model
        self._resolved_model = resolve_model(model, settings)

    @property
    def provider_id(self) -> str:
        return "litellm"

    @property
    def model_name(self) -> str:
        return self._configured_model

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            structured_json=True,
            json_schema=True,
            tool_calling=True,
            streaming=True,
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        try:
            import litellm
        except ImportError as exc:
            raise LLMConfigurationError(
                'LiteLLM not installed. Use: pip install -e ".[llm-litellm]"'
            ) from exc

        litellm.drop_params = True
        started = time.perf_counter()
        resolved = resolve_model(self._configured_model, self._settings)
        logger.info(
            "LLM request: provider=%s model=%s litellm_model=%s prompt_version=%s timeout_s=%s",
            self.provider_id,
            self._configured_model,
            resolved,
            request.prompt_version,
            request.timeout_seconds,
        )

        messages = [
            {"role": "system", "content": request.system_instruction},
            {"role": "user", "content": request.user_prompt},
        ]

        def _call() -> tuple[str, str | None, int | None, int | None]:
            completion_kwargs: dict = {
                "model": resolved,
                "messages": messages,
                "temperature": request.temperature,
                "timeout": request.timeout_seconds,
                "num_retries": 0,
            }
            if request.max_output_tokens > 0:
                completion_kwargs["max_tokens"] = request.max_output_tokens
            response = litellm.completion(**completion_kwargs)
            choice = response.choices[0]
            content = (choice.message.content or "").strip()
            if not content:
                logger.warning(
                    "LiteLLM empty message.content (finish_reason=%s model=%s)",
                    choice.finish_reason,
                    resolved,
                )
            usage = getattr(response, "usage", None)
            in_tok = getattr(usage, "prompt_tokens", None) if usage else None
            out_tok = getattr(usage, "completion_tokens", None) if usage else None
            return content, choice.finish_reason, in_tok, out_tok

        try:
            raw, finish_reason, in_tok, out_tok = await asyncio.to_thread(_call)
        except Exception as exc:
            latency = (time.perf_counter() - started) * 1000
            logger.warning(
                "LiteLLM request failed: model=%s latency_ms=%.0f error=%s",
                resolved,
                latency,
                type(exc).__name__,
            )
            raise LLMProviderError(
                f"LiteLLM request failed: {exc}",
                provider=self.provider_id,
                retryable=True,
            ) from exc

        latency = (time.perf_counter() - started) * 1000
        return LLMResponse(
            raw_text=raw,
            provider=self.provider_id,
            model=self._configured_model,
            prompt_version=request.prompt_version,
            latency_ms=latency,
            input_tokens=in_tok,
            output_tokens=out_tok,
            finish_reason=finish_reason,
            success=True,
        )

    async def health_check(self) -> bool:
        try:
            import litellm
        except ImportError:
            return False
        try:
            resolved = resolve_model(self._configured_model, self._settings)

            def _ping() -> bool:
                litellm.completion(
                    model=resolved,
                    messages=[{"role": "user", "content": "ping"}],
                    max_tokens=1,
                    timeout=15,
                    num_retries=0,
                )
                return True

            return await asyncio.to_thread(_ping)
        except Exception:
            return False

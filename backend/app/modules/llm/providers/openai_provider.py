"""OpenAI adapter."""

import asyncio
import logging
import time

from app.core.config import Settings
from app.modules.llm.configuration.capabilities import ProviderCapabilities
from app.modules.llm.exceptions import LLMConfigurationError, LLMProviderError
from app.modules.llm.interfaces.base_provider import BaseLLMProvider
from app.modules.llm.interfaces.llm_schemas import LLMRequest, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, settings: Settings) -> None:
        api_key = (settings.OPENAI_API_KEY or "").strip()
        if not api_key:
            raise LLMConfigurationError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        model = (settings.LLM_MODEL or "").strip()
        if not model:
            raise LLMConfigurationError("LLM_MODEL is required when LLM_PROVIDER=openai")
        self._api_key = api_key
        self._model = model
        self._base_url = (settings.OPENAI_BASE_URL or "").strip() or None
        self._sdk_max_retries = max(0, settings.LLM_OPENAI_SDK_MAX_RETRIES)

    @property
    def provider_id(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            structured_json=True,
            json_schema=True,
            tool_calling=True,
            streaming=True,
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMConfigurationError(
                'openai SDK not installed. Use: pip install -e ".[llm-openai]"'
            ) from exc

        started = time.perf_counter()
        logger.info(
            "LLM request: provider=%s model=%s prompt_version=%s base_url=%s "
            "timeout_s=%s max_output_tokens=%s sdk_max_retries=%s",
            self.provider_id,
            self._model,
            request.prompt_version,
            "custom" if self._base_url else "default",
            request.timeout_seconds,
            request.max_output_tokens,
            self._sdk_max_retries,
        )
        client = OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
            max_retries=self._sdk_max_retries,
            timeout=request.timeout_seconds,
        )

        def _call() -> tuple[str, str | None, int | None, int | None, str | None]:
            create_kwargs: dict = {
                "model": self._model,
                "temperature": request.temperature,
                "messages": [
                    {"role": "system", "content": request.system_instruction},
                    {"role": "user", "content": request.user_prompt},
                ],
            }
            if request.max_output_tokens > 0:
                create_kwargs["max_tokens"] = request.max_output_tokens
                create_kwargs["response_format"] = {"type": "json_object"}
            completion = client.chat.completions.create(**create_kwargs)
            choice = completion.choices[0]
            content = (choice.message.content or "").strip()
            if not content:
                logger.warning(
                    "LLM empty message.content (finish_reason=%s); gateway may use a non-standard field",
                    choice.finish_reason,
                )
                content = "{}"
            usage = completion.usage
            in_tok = usage.prompt_tokens if usage else None
            out_tok = usage.completion_tokens if usage else None
            req_id = getattr(completion, "id", None)
            return content, choice.finish_reason, in_tok, out_tok, req_id

        try:
            raw, finish_reason, in_tok, out_tok, req_id = await asyncio.to_thread(_call)
        except Exception as exc:
            latency = (time.perf_counter() - started) * 1000
            logger.warning(
                "LLM request failed: provider=%s model=%s latency_ms=%.0f error=%s",
                self.provider_id,
                self._model,
                latency,
                type(exc).__name__,
            )
            raise LLMProviderError(
                f"OpenAI request failed: {exc}",
                provider=self.provider_id,
                retryable=True,
            ) from exc

        latency = (time.perf_counter() - started) * 1000
        logger.info(
            "LLM request complete: provider=%s model=%s latency_ms=%.0f bytes=%s "
            "finish_reason=%s output_tokens=%s",
            self.provider_id,
            self._model,
            latency,
            len(raw),
            finish_reason,
            out_tok,
        )
        return LLMResponse(
            raw_text=raw,
            provider=self.provider_id,
            model=self._model,
            prompt_version=request.prompt_version,
            latency_ms=latency,
            input_tokens=in_tok,
            output_tokens=out_tok,
            request_id=req_id,
            finish_reason=finish_reason,
            success=True,
        )

    async def health_check(self) -> bool:
        try:
            from openai import OpenAI
        except ImportError:
            return False
        try:
            client = OpenAI(api_key=self._api_key, base_url=self._base_url)
            await asyncio.to_thread(lambda: client.models.list())
            return True
        except Exception:
            return False

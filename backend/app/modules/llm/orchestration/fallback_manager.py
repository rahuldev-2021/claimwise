"""Retry and optional fallback provider selection."""

import asyncio
import logging

from app.core.config import Settings
from app.modules.llm.exceptions import LLMProviderError
from app.modules.llm.factory.provider_factory import ProviderFactory
from app.modules.llm.interfaces.base_provider import BaseLLMProvider
from app.modules.llm.interfaces.llm_schemas import LLMRequest, LLMResponse

logger = logging.getLogger(__name__)


class FallbackManager:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def execute(
        self,
        request: LLMRequest,
        primary: BaseLLMProvider,
    ) -> tuple[LLMResponse | None, str, str, list[str]]:
        """Returns response, provider used, model used, attempt notes."""
        attempts: list[str] = []
        max_retries = max(0, self._settings.LLM_MAX_RETRIES)
        providers: list[BaseLLMProvider] = [primary]

        fallback_name = (self._settings.LLM_FALLBACK_PROVIDER or "").strip().lower()
        if fallback_name and fallback_name != primary.provider_id:
            try:
                providers.append(ProviderFactory.create(self._settings, provider_name=fallback_name))
            except Exception as exc:
                attempts.append(f"fallback_config_error:{exc}")

        for provider in providers:
            for attempt in range(max_retries + 1):
                label = f"{provider.provider_id}:{attempt}"
                try:
                    response = await provider.generate(request)
                    attempts.append(f"success:{label}")
                    used = provider.provider_id
                    if provider.provider_id != primary.provider_id:
                        attempts.append("fallback_activated")
                    return response, used, provider.model_name, attempts
                except LLMProviderError as exc:
                    attempts.append(f"provider_error:{label}:{exc}")
                    if not exc.retryable or attempt >= max_retries:
                        break
                    await asyncio.sleep(0.05 * (attempt + 1))
                except Exception as exc:
                    attempts.append(f"error:{label}:{exc}")
                    break

        return None, primary.provider_id, primary.model_name, attempts

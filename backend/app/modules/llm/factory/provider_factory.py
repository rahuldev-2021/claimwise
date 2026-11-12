"""Instantiate LLM providers from settings."""

from typing import Callable

from app.core.config import Settings
from app.modules.llm.exceptions import LLMConfigurationError
from app.modules.llm.interfaces.base_provider import BaseLLMProvider
from app.modules.llm.providers.anthropic_provider import AnthropicProvider
from app.modules.llm.providers.gemini_provider import GeminiProvider
from app.modules.llm.providers.mock_provider import MockLLMProvider
from app.modules.llm.providers.ollama_provider import OllamaProvider
from app.modules.llm.providers.litellm_provider import LiteLLMProvider
from app.modules.llm.providers.openai_provider import OpenAIProvider

_REGISTRY: dict[str, Callable[[Settings], BaseLLMProvider]] = {
    "mock": lambda s: MockLLMProvider(model=s.LLM_MODEL or "mock-model"),
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "litellm": LiteLLMProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
}

SUPPORTED_PROVIDERS = frozenset(_REGISTRY.keys())


class ProviderFactory:
    @staticmethod
    def create(settings: Settings, *, provider_name: str | None = None) -> BaseLLMProvider:
        name = (provider_name or settings.LLM_PROVIDER or "").strip().lower()
        if not name:
            raise LLMConfigurationError("LLM_PROVIDER is not configured")
        if name not in _REGISTRY:
            raise LLMConfigurationError(
                f"Unsupported LLM_PROVIDER '{name}'. Supported: {', '.join(sorted(SUPPORTED_PROVIDERS))}"
            )
        return _REGISTRY[name](settings)

    @staticmethod
    def validate_settings(settings: Settings, *, provider_name: str | None = None) -> None:
        """Validate configuration for the selected provider without calling external APIs."""
        ProviderFactory.create(settings, provider_name=provider_name)

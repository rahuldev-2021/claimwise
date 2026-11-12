"""Resolve Phase 5 LLM provider for NLP fallback."""

from app.core.config import Settings
from app.modules.llm.factory.provider_factory import ProviderFactory
from app.modules.llm.interfaces.base_provider import BaseLLMProvider


def create_nlp_llm_provider(settings: Settings) -> BaseLLMProvider:
    name = (settings.LLM_NLP_PROVIDER or settings.LLM_PROVIDER or "").strip()
    effective = settings
    if settings.LLM_NLP_MODEL:
        effective = effective.model_copy(update={"LLM_MODEL": settings.LLM_NLP_MODEL})
    if settings.LLM_NLP_TIMEOUT_SECONDS:
        effective = effective.model_copy(
            update={"LLM_TIMEOUT_SECONDS": settings.LLM_NLP_TIMEOUT_SECONDS}
        )
    if settings.LLM_NLP_MAX_OUTPUT_TOKENS:
        effective = effective.model_copy(
            update={"LLM_MAX_OUTPUT_TOKENS": settings.LLM_NLP_MAX_OUTPUT_TOKENS}
        )
    return ProviderFactory.create(effective, provider_name=name or None)

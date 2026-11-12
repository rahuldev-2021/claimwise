import pytest

from app.core.config import Settings
from app.modules.llm.exceptions import LLMConfigurationError
from app.modules.llm.factory.provider_factory import ProviderFactory
from app.modules.llm.providers.mock_provider import MockLLMProvider


def test_factory_selects_mock():
    settings = Settings(LLM_PROVIDER="mock", LLM_MODEL="test-mock")
    provider = ProviderFactory.create(settings)
    assert isinstance(provider, MockLLMProvider)
    assert provider.provider_id == "mock"


def test_unsupported_provider_raises():
    settings = Settings(LLM_PROVIDER="unknown")
    with pytest.raises(LLMConfigurationError, match="Unsupported"):
        ProviderFactory.create(settings)


def test_gemini_missing_key_raises():
    settings = Settings(LLM_PROVIDER="gemini", GEMINI_API_KEY="")
    with pytest.raises(LLMConfigurationError, match="GEMINI_API_KEY"):
        ProviderFactory.create(settings)

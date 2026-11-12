import os

import pytest

from app.core.config import Settings
from app.modules.llm.factory.provider_factory import ProviderFactory
from app.modules.llm.interfaces.llm_schemas import LLMRequest

pytestmark = pytest.mark.llm_live


@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
def test_gemini_generate_json():
    settings = Settings(
        LLM_ENABLED=True,
        LLM_PROVIDER="gemini",
        LLM_MODEL=os.getenv("GEMINI_LIVE_MODEL", "gemini-2.0-flash"),
        GEMINI_API_KEY=os.getenv("GEMINI_API_KEY", ""),
    )
    provider = ProviderFactory.create(settings)
    response = provider.generate_sync(
        LLMRequest(
            system_instruction='Respond with JSON: {"ok": true}',
            user_prompt='Return {"ok": true}',
            max_output_tokens=64,
        )
    )
    assert response.success
    assert "{" in response.raw_text

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.modules.llm.exceptions import LLMConfigurationError
from app.modules.llm.factory.provider_factory import ProviderFactory, SUPPORTED_PROVIDERS
from app.modules.llm.litellm_runtime import normalize_openai_base_url, resolve_litellm_model

router = APIRouter(tags=["llm"])
_settings = get_settings()


@router.get("/llm/health")
def llm_health():
    configured_model = _settings.effective_llm_model()
    body = {
        "llm_enabled": _settings.LLM_ENABLED,
        "configured_provider": _settings.LLM_PROVIDER,
        "configured_model": configured_model,
        "litellm_resolved_model": resolve_litellm_model(configured_model, _settings)
        if configured_model
        else "",
        "gateway_base_url": normalize_openai_base_url(
            _settings.CHATGPT_BASE_URL or _settings.OPENAI_BASE_URL
        )
        or "",
        "supported_providers": sorted(SUPPORTED_PROVIDERS),
        "provider_ready": False,
        "capabilities": {},
    }
    if not _settings.LLM_ENABLED:
        return body

    try:
        provider = ProviderFactory.create(_settings)
        body["configured_model"] = body["configured_model"] or provider.model_name
        caps = provider.capabilities().model_dump()
        body["capabilities"] = caps
        body["provider_ready"] = provider.health_check_sync()
        return body
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

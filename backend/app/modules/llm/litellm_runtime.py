"""LiteLLM env bootstrap and model resolution (OpenAI-compatible gateways / Lucius parity)."""

import os

from app.core.config import Settings


def normalize_openai_base_url(base_url: str | None) -> str | None:
    if not base_url:
        return None
    url = base_url.strip().rstrip("/")
    if url.endswith("/chat/completions"):
        url = url[: -len("/chat/completions")]
    return url or None


def _resolve_api_key(settings: Settings) -> str:
    return (
        (settings.CHATGPT_API_KEY or "").strip()
        or (settings.OPENAI_API_KEY or "").strip()
        or (os.getenv("CHATGPT_API_KEY") or "").strip()
        or (os.getenv("OPENAI_API_KEY") or "").strip()
        or (os.getenv("LLM_API_KEY") or "").strip()
    )


def _resolve_base_url(settings: Settings) -> str | None:
    raw = (
        (settings.CHATGPT_BASE_URL or "").strip()
        or (settings.OPENAI_BASE_URL or "").strip()
        or (os.getenv("CHATGPT_BASE_URL") or "").strip()
        or (os.getenv("OPENAI_BASE_URL") or "").strip()
    )
    return normalize_openai_base_url(raw) if raw else None


def _resolve_raw_model(settings: Settings, model: str | None = None) -> str:
    return (
        (model or "").strip()
        or settings.effective_llm_model()
        or (os.getenv("CHATGPT_MODEL") or "").strip()
        or (os.getenv("LLM_MODEL") or "").strip()
        or (os.getenv("OPENAI_MODEL") or "").strip()
    )


def bootstrap_llm_environment(settings: Settings) -> None:
    """Align process env with LiteLLM before any completion (call at app startup)."""
    key = _resolve_api_key(settings)
    if key:
        os.environ.setdefault("OPENAI_API_KEY", key)

    base = _resolve_base_url(settings)
    if base:
        os.environ["OPENAI_BASE_URL"] = base
        os.environ["OPENAI_API_BASE"] = base
        os.environ["CHATGPT_BASE_URL"] = base

    model = _resolve_raw_model(settings)
    if model:
        os.environ.setdefault("CHATGPT_MODEL", model)
        os.environ.setdefault("LLM_MODEL", model)


def resolve_litellm_model(model: str | None, settings: Settings) -> str:
    """Bare gateway id → `openai/qwen-coder-2` when a custom base URL is set."""
    raw = _resolve_raw_model(settings, model)
    if not raw:
        return raw
    if raw.startswith("litellm/"):
        raw = raw.removeprefix("litellm/")
    if "/" in raw and not raw.startswith("openai/"):
        return raw
    base = _resolve_base_url(settings) or os.getenv("OPENAI_BASE_URL")
    if base and not raw.startswith("openai/"):
        return f"openai/{raw}"
    return raw


def resolve_model(model: str | None, settings: Settings) -> str:
    """Public alias (Lucius `resolve_model` parity)."""
    resolved = resolve_litellm_model(model, settings)
    if resolved.startswith("litellm/"):
        return resolved.removeprefix("litellm/")
    return resolved

from app.core.config import Settings
from app.modules.llm.litellm_runtime import normalize_openai_base_url, resolve_litellm_model


def test_strips_chat_completions_suffix():
    assert normalize_openai_base_url("https://host/v1/chat/completions") == "https://host/v1"


def test_openai_prefix_for_custom_gateway():
    s = Settings(
        OPENAI_BASE_URL="http://gateway/v1",
        LLM_MODEL="qwen-coder-2",
    )
    assert resolve_litellm_model("qwen-coder-2", s) == "openai/qwen-coder-2"


def test_chatgpt_aliases_strip_completions_and_resolve():
    s = Settings(
        CHATGPT_API_KEY="none",
        CHATGPT_BASE_URL="http://1.6.37.57/gateway/mlflow/v1/chat/completions",
        CHATGPT_MODEL="qwen-coder-2",
        LLM_PROVIDER="litellm",
    )
    assert s.OPENAI_API_KEY == "none"
    assert s.OPENAI_BASE_URL == "http://1.6.37.57/gateway/mlflow/v1"
    assert s.LLM_MODEL == "qwen-coder-2"
    assert resolve_litellm_model(None, s) == "openai/qwen-coder-2"

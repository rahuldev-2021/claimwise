from pydantic import model_validator
from pydantic_settings import BaseSettings


def _normalize_gateway_base_url(base_url: str) -> str:
    url = base_url.strip().rstrip("/")
    if url.endswith("/chat/completions"):
        url = url[: -len("/chat/completions")]
    return url


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    APP_NAME: str = "CLAIMWISE"
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    SAMPLE_DATA_DIR: str = "data/sample"
    NLP_FUZZY_MATCH_THRESHOLD: float = 0.86
    NLP_FUZZY_MATCHER: str = "difflib"
    NLP_ENABLE_SPACY: bool = True
    NLP_CONTEXTUAL_PROVIDER: str = ""

    LLM_NLP_ENABLED: bool = False
    LLM_NLP_FALLBACK_MODE: str = "conditional"
    LLM_NLP_PROVIDER: str = ""
    LLM_NLP_MODEL: str = ""
    LLM_NLP_TIMEOUT_SECONDS: float = 120.0
    LLM_NLP_MAX_RETRIES: int = 1
    LLM_NLP_MIN_TRIGGER_COUNT: int = 2
    LLM_NLP_MAX_INPUT_TOKENS: int = 4096
    LLM_NLP_MAX_OUTPUT_TOKENS: int = 1536

    RAG_FILTER_MODE: str = "balanced"
    RAG_MIN_PASSAGES_FALLBACK: int = 2
    RAG_CLAIM_HARD_FILTER_FIELDS: str = (
        "repair_category,vehicle_make,vehicle_model,model_year"
    )

    RAG_PERSIST_DIR: str = "data/rag/chroma"
    RAG_COLLECTION_NAME: str = "claimwise_rag"
    RAG_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 100
    RAG_RRF_K: int = 60
    RAG_RETRIEVAL_DEPTH: int = 20
    RAG_RELEVANCE_THRESHOLD: float = 0.0
    RAG_DEFAULT_MODE: str = "advanced"
    RAG_SCOPE_FETCH_MULTIPLIER: int = 4
    RAG_UPLOAD_MIN_TEXT_CHARS: int = 40
    RAG_INVESTIGATION_ENABLED: bool = True
    RAG_WORKER_AUTO_INGEST_SAMPLE: bool = False
    RAG_STARTUP_INGEST: bool = True
    INVESTIGATION_RUN_TECHNICAL_VALIDATION: bool = True
    INVESTIGATION_SKIP_TV_IF_PRESENT: bool = True
    HISTORICAL_REPAIRS_INGEST_ENABLED: bool = False

    TV_DEFAULT_TOP_K: int = 5
    TV_RETRIEVAL_MODE: str = "advanced"
    TV_AUTO_INGEST: bool = False

    LLM_ENABLED: bool = False
    LLM_PROVIDER: str = "mock"
    LLM_MODEL: str = ""
    LLM_TEMPERATURE: float = 0.2
    # 0 = do not send max_tokens to the gateway (let the model default).
    LLM_MAX_OUTPUT_TOKENS: int = 0
    LLM_TV_TEMPLATE_FALLBACK: bool = True
    LLM_TIMEOUT_SECONDS: float = 30.0
    LLM_MAX_RETRIES: int = 1
    LLM_COMPACT_CONTEXT: bool = True
    LLM_JSON_REPAIR_ENABLED: bool = True
    LLM_RAW_OUTPUT_LOG_CHARS: int = 3000
    LLM_RAW_OUTPUT_PREVIEW_CHARS: int = 4000
    LLM_OPENAI_SDK_MAX_RETRIES: int = 0
    LLM_FALLBACK_PROVIDER: str = ""
    LLM_FALLBACK_MODEL: str = ""
    LLM_PROMPT_VERSION: str = ""
    LLM_SCHEMA_VERSION: str = "assessment_schema_v2"
    LLM_CONTEXT_MAX_CHARS: int = 12000
    LLM_CONTEXT_MAX_PASSAGES: int = 8
    LLM_RECOMMENDATION_HISTORY_MAX: int = 20
    PHASE5_REUSE_CACHED_STAGES: bool = True
    PHASE5_REUSE_LLM_IF_FINGERPRINT_MATCH: bool = True

    GEMINI_API_KEY: str = ""
    # Lucius-style gateway aliases (source of truth when set)
    CHATGPT_API_KEY: str = ""
    CHATGPT_BASE_URL: str = ""
    CHATGPT_MODEL: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    ANTHROPIC_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    FEEDBACK_DATA_PATH: str = "data/reviewer_feedback.json"

    FINANCIAL_ENABLED: bool = True
    FINANCIAL_CONFIG_DIR: str = "config/financial"
    FINANCIAL_MODEL_REGISTRY_DIR: str = "data/financial_models"
    FINANCIAL_TRAINING_DATA_PATH: str = ""
    FINANCIAL_REQUIRE_MODELS: bool = False
    FINANCIAL_EXPERIMENTAL_MODELS_ENABLED: bool = False
    FINANCIAL_EXPERIMENTAL_REGISTRY_DIR: str = (
        "data/financial_models/synthetic_v1/experimental_artifacts"
    )

    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "claimwise"

    CLAIMS_UPLOAD_DIR: str = "data/uploads"
    CLAIMS_MAX_FILE_BYTES: int = 10 * 1024 * 1024
    CLAIMS_MAX_TOTAL_UPLOAD_BYTES: int = 50 * 1024 * 1024
    CLAIMS_MAX_FILES: int = 10

    JOB_LEASE_SECONDS: int = 300
    JOB_BASE_RETRY_SECONDS: int = 30
    JOB_MAX_ATTEMPTS: int = 5
    WORKER_POLL_INTERVAL_MS: int = 2000
    # When True, the API process polls the job queue (no separate `python -m app.worker`).
    EMBED_CLAIM_WORKER: bool = True

    JWT_SECRET: str = ""
    JWT_ISSUER: str = "claimwise"
    JWT_AUDIENCE: str = "claimwise-app"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    AUTH_COOKIE_SECURE: bool = False
    AUTH_COOKIE_SAMESITE: str = "lax"
    AUTH_REFRESH_COOKIE_NAME: str = "refresh_token"

    AUTH_BOOTSTRAP_ADMIN_EMAIL: str = "AdminUser2021@gmail.com"
    AUTH_BOOTSTRAP_ADMIN_PASSWORD: str = "Mymail@2021146"
    AUTH_BOOTSTRAP_ORG_NAME: str = "Ford Claim Assistant"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @model_validator(mode="after")
    def apply_chatgpt_aliases(self) -> "Settings":
        """Map CHATGPT_* (MLflow gateway) onto OPENAI_* / LLM_MODEL like Lucius."""
        if (self.CHATGPT_API_KEY or "").strip():
            object.__setattr__(self, "OPENAI_API_KEY", self.CHATGPT_API_KEY.strip())
        if (self.CHATGPT_BASE_URL or "").strip():
            normalized = _normalize_gateway_base_url(self.CHATGPT_BASE_URL)
            object.__setattr__(
                self, "OPENAI_BASE_URL", normalized or self.CHATGPT_BASE_URL.strip()
            )
        if (self.CHATGPT_MODEL or "").strip():
            object.__setattr__(self, "LLM_MODEL", self.CHATGPT_MODEL.strip())
        return self

    def effective_llm_model(self) -> str:
        return (self.LLM_MODEL or self.CHATGPT_MODEL or "").strip()


def get_settings() -> Settings:
    return Settings()

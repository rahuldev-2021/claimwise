from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.health import router as health_router
from app.api.routes.nlp import router as nlp_router
from app.api.routes.rag import router as rag_router
from app.api.routes.technical_validation import router as technical_validation_router
from app.api.routes.assessment import router as assessment_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.llm import router as llm_router
from app.api.routes.claims import router as claims_router
from app.api.routes.financial_validation import router as financial_validation_router
from app.api.routes.reviewer_feedback import router as reviewer_feedback_router
from app.auth.routes import router as auth_router
from app.auth.mongodb import get_auth_db
from app.auth.seed import seed_auth_data
from app.core.config import get_settings
from app.core.logging_config import configure_logging

settings = get_settings()
configure_logging(settings.LOG_LEVEL)

if settings.APP_ENV != "test":
    from app.modules.llm.litellm_runtime import bootstrap_llm_environment

    bootstrap_llm_environment(settings)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    import logging

    log = logging.getLogger(__name__)
    worker_stop = None

    if settings.JWT_SECRET.strip():
        try:
            seed_auth_data(get_auth_db(settings), settings)
        except Exception:
            log.exception("Auth seed skipped — is MongoDB running and JWT_SECRET set?")

    if settings.RAG_STARTUP_INGEST and settings.APP_ENV != "test":
        try:
            from app.services.rag_service_provider import get_rag_service

            report = get_rag_service(settings).ensure_startup_corpus()
            if report is not None:
                log.info(
                    "RAG startup ingest complete: indexed=%d duplicate=%d chunks=%d",
                    report.indexed,
                    report.skipped_duplicate,
                    report.total_chunks,
                )
        except Exception:
            log.exception("RAG startup ingest failed — retrieval may return 503 until ingest succeeds")

    if settings.EMBED_CLAIM_WORKER:
        try:
            from app.worker import start_embedded_worker

            _, worker_stop = start_embedded_worker(settings)
            log.info(
                "Embedded claim investigation worker enabled (EMBED_CLAIM_WORKER=true)"
            )
        except Exception:
            log.exception("Embedded claim worker failed to start — is MongoDB running?")

    yield

    if worker_stop is not None:
        worker_stop.set()


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Driven Automotive Repair Claim Validation and Decision Support System",
    version="0.1.0",
    lifespan=lifespan,
)

_cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
_cors_origin_regex: str | None = None
if settings.APP_ENV == "development" or settings.DEBUG:
    # Vite may use 5174+ when 5173 is busy; allow any local dev UI origin.
    _cors_origin_regex = r"https?://(localhost|127\.0\.0\.1)(:\d+)?"

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=_cors_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Device-Id"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(nlp_router, prefix=settings.API_PREFIX)
app.include_router(rag_router, prefix=settings.API_PREFIX)
app.include_router(technical_validation_router, prefix=settings.API_PREFIX)
app.include_router(assessment_router, prefix=settings.API_PREFIX)
app.include_router(recommendations_router, prefix=settings.API_PREFIX)
app.include_router(llm_router, prefix=settings.API_PREFIX)
app.include_router(claims_router, prefix=settings.API_PREFIX)
app.include_router(reviewer_feedback_router, prefix=settings.API_PREFIX)
app.include_router(financial_validation_router, prefix=settings.API_PREFIX)


def run() -> None:
    """Start the HTTP server (use: python main.py from the backend directory)."""
    import uvicorn

    reload = settings.APP_ENV == "development" or settings.DEBUG
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=reload,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    run()

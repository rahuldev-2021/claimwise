"""Shared dependencies for claim routes."""

from functools import lru_cache

from app.auth.mongodb import get_auth_db
from app.core.config import Settings, get_settings
from app.jobs.mongo_job_queue import MongoJobQueue
from app.modules.claim_documents.blob_store import LocalBlobStore
from app.repositories.mongo_claim_repository import MongoClaimRepository
from app.services.claim_intake_service import ClaimIntakeService
from app.services.claim_service import ClaimService


@lru_cache
def get_claim_service() -> ClaimService:
    return ClaimService(get_settings())


def get_intake_service(settings: Settings | None = None) -> ClaimIntakeService:
    settings = settings or get_settings()
    db = get_auth_db(settings)
    return ClaimIntakeService(
        settings,
        MongoClaimRepository(db),
        MongoJobQueue(
            db,
            lease_seconds=settings.JOB_LEASE_SECONDS,
            base_retry_seconds=settings.JOB_BASE_RETRY_SECONDS,
        ),
        LocalBlobStore(settings),
    )


def get_blob_store(settings: Settings | None = None) -> LocalBlobStore:
    return LocalBlobStore(settings or get_settings())

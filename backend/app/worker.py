"""Background worker: poll MongoDB job queue and run investigation handlers."""

from __future__ import annotations

import logging
import sys
import threading
import time
from typing import Optional

from app.auth.mongodb import get_auth_db
from app.core.config import Settings, get_settings
from app.jobs.mongo_job_queue import MongoJobQueue
from app.jobs.schemas import JobType
from app.modules.claim_documents.blob_store import LocalBlobStore
from app.repositories.mongo_claim_repository import MongoClaimRepository
from app.repositories.mongo_repair_document_repository import MongoRepairDocumentRepository
from app.services.investigation_handler import InvestigationHandler

logger = logging.getLogger(__name__)


def recover_outbox(claims: MongoClaimRepository, jobs: MongoJobQueue, max_attempts: int) -> None:
    for record in claims.find_unprocessed_outbox():
        for ev in record.outbox:
            if ev.processed:
                continue
            idempotency_key = f"{JobType.CLAIM_INVESTIGATION.value}:{record.claim_id}:v1"
            try:
                job = jobs.enqueue(
                    claim_id=record.claim_id,
                    org_id=record.org_id,
                    idempotency_key=idempotency_key,
                    max_attempts=max_attempts,
                )
                claims.mark_outbox_processed(record.claim_id, record.org_id, job.job_id)
            except Exception:
                logger.exception("Outbox recovery failed for %s", record.claim_id)


class ClaimInvestigationWorker:
    """Polls MongoDB jobs and runs the investigation pipeline."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        settings = settings or get_settings()
        self._settings = settings
        db = get_auth_db(settings)
        self._claims = MongoClaimRepository(db)
        self._jobs = MongoJobQueue(
            db,
            lease_seconds=settings.JOB_LEASE_SECONDS,
            base_retry_seconds=settings.JOB_BASE_RETRY_SECONDS,
        )
        self._handler = InvestigationHandler(
            settings,
            self._claims,
            MongoRepairDocumentRepository(db),
            LocalBlobStore(settings),
        )
        self._interval = max(100, settings.WORKER_POLL_INTERVAL_MS) / 1000.0

    def run_once(self) -> bool:
        """Recover outbox, then process at most one job. Returns True if a job was leased."""
        recover_outbox(self._claims, self._jobs, self._settings.JOB_MAX_ATTEMPTS)
        job = self._jobs.lease_next()
        if not job:
            return False
        if job.job_type != JobType.CLAIM_INVESTIGATION:
            self._jobs.fail(job, f"Unsupported job type: {job.job_type}")
            return True
        try:
            self._handler.run(job)
            self._jobs.complete(job.job_id)
            logger.info("Job %s completed for claim %s", job.job_id, job.claim_id)
        except Exception as exc:
            logger.exception("Job %s failed for claim %s", job.job_id, job.claim_id)
            self._jobs.fail(job, str(exc))
        return True

    def run_until_stopped(self, stop: threading.Event) -> None:
        logger.info("CLAIMWISE investigation worker started (poll %.1fs)", self._interval)
        while not stop.is_set():
            try:
                processed = self.run_once()
                if not processed:
                    stop.wait(self._interval)
            except Exception:
                logger.exception("Worker loop error")
                stop.wait(self._interval)
        logger.info("CLAIMWISE investigation worker stopped")


def start_embedded_worker(settings: Optional[Settings] = None) -> tuple[threading.Thread, threading.Event]:
    """Daemon thread for use inside the API process."""
    stop = threading.Event()
    worker = ClaimInvestigationWorker(settings)

    def _target() -> None:
        worker.run_until_stopped(stop)

    thread = threading.Thread(target=_target, name="claim-investigation-worker", daemon=True)
    thread.start()
    return thread, stop


def run_worker() -> None:
    """Standalone worker entrypoint (`python -m app.worker`)."""
    settings = get_settings()
    logging.basicConfig(level=settings.LOG_LEVEL)
    stop = threading.Event()
    worker = ClaimInvestigationWorker(settings)
    try:
        worker.run_until_stopped(stop)
    except KeyboardInterrupt:
        logger.info("Worker stopping")
        stop.set()
        sys.exit(0)


if __name__ == "__main__":
    run_worker()

"""MongoDB-backed job queue with lease, retry, and stuck recovery."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from pymongo import ASCENDING, ReturnDocument
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.jobs.schemas import JobRecord, JobStatus, JobType


class MongoJobQueue:
    COLLECTION = "jobs"

    def __init__(
        self,
        db: Database,
        *,
        lease_seconds: int = 300,
        base_retry_seconds: int = 30,
    ) -> None:
        self._col = db[self.COLLECTION]
        self._lease_seconds = lease_seconds
        self._base_retry_seconds = base_retry_seconds
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self._col.create_index("job_id", unique=True)
        try:
            self._col.create_index("idempotency_key", unique=True, sparse=True)
        except Exception:
            pass
        self._col.create_index([("status", ASCENDING), ("next_retry_at", ASCENDING)])

    def enqueue(
        self,
        *,
        claim_id: str,
        org_id: str,
        job_type: JobType = JobType.CLAIM_INVESTIGATION,
        idempotency_key: str,
        max_attempts: int = 5,
        job_id: str | None = None,
        session=None,
    ) -> JobRecord:
        job = JobRecord(
            job_id=job_id or str(uuid4()),
            claim_id=claim_id,
            org_id=org_id,
            job_type=job_type,
            idempotency_key=idempotency_key,
            max_attempts=max_attempts,
        )
        try:
            self._col.insert_one(job.model_dump(mode="json"), session=session)
        except DuplicateKeyError:
            existing = self._col.find_one({"idempotency_key": idempotency_key})
            if existing:
                return JobRecord.model_validate(existing)
            raise
        return job

    def lease_next(self) -> Optional[JobRecord]:
        now = datetime.now(timezone.utc)
        self.recover_stuck_jobs()
        lease_until = now + timedelta(seconds=self._lease_seconds)
        doc = self._col.find_one_and_update(
            {
                "status": {"$in": [JobStatus.PENDING.value, JobStatus.FAILED.value]},
                "$or": [
                    {"next_retry_at": None},
                    {"next_retry_at": {"$lte": now.isoformat()}},
                ],
            },
            {
                "$set": {
                    "status": JobStatus.PROCESSING.value,
                    "started_at": now.isoformat(),
                    "lease_expires_at": lease_until.isoformat(),
                },
                "$inc": {"attempt_count": 1},
            },
            sort=[("created_at", ASCENDING)],
            return_document=ReturnDocument.AFTER,
        )
        return JobRecord.model_validate(doc) if doc else None

    def complete(self, job_id: str) -> None:
        now = datetime.now(timezone.utc)
        self._col.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": JobStatus.COMPLETED.value,
                    "completed_at": now.isoformat(),
                    "lease_expires_at": None,
                    "last_error": None,
                }
            },
        )

    def fail(self, job: JobRecord, error: str) -> None:
        now = datetime.now(timezone.utc)
        dead = job.attempt_count >= job.max_attempts
        backoff = self._base_retry_seconds * (2 ** max(0, job.attempt_count - 1))
        next_retry = now + timedelta(seconds=min(backoff, 3600))
        self._col.update_one(
            {"job_id": job.job_id},
            {
                "$set": {
                    "status": JobStatus.DEAD.value if dead else JobStatus.FAILED.value,
                    "last_error": error[:2000],
                    "lease_expires_at": None,
                    "next_retry_at": None if dead else next_retry.isoformat(),
                    "completed_at": now.isoformat() if dead else None,
                }
            },
        )

    def recover_stuck_jobs(self) -> int:
        now = datetime.now(timezone.utc)
        result = self._col.update_many(
            {
                "status": JobStatus.PROCESSING.value,
                "lease_expires_at": {"$lt": now.isoformat()},
            },
            {
                "$set": {
                    "status": JobStatus.PENDING.value,
                    "lease_expires_at": None,
                }
            },
        )
        return result.modified_count

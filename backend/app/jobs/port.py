"""Job queue port (adapter: MongoJobQueue)."""

from typing import Optional, Protocol

from app.jobs.schemas import JobRecord, JobType


class JobQueue(Protocol):
    def enqueue(
        self,
        *,
        claim_id: str,
        org_id: str,
        job_type: JobType = JobType.CLAIM_INVESTIGATION,
        idempotency_key: str,
        max_attempts: int = 5,
    ) -> JobRecord: ...

    def lease_next(self) -> Optional[JobRecord]: ...

    def complete(self, job_id: str) -> None: ...

    def fail(self, job: JobRecord, error: str) -> None: ...

    def recover_stuck_jobs(self) -> int: ...

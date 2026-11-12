"""Background job queue models."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DEAD = "DEAD"


class JobType(str, Enum):
    CLAIM_INVESTIGATION = "CLAIM_INVESTIGATION"


class JobRecord(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid4()))
    claim_id: str
    org_id: str
    job_type: JobType = JobType.CLAIM_INVESTIGATION
    status: JobStatus = JobStatus.PENDING
    attempt_count: int = 0
    max_attempts: int = 5
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    last_error: Optional[str] = None
    idempotency_key: str = ""
    lease_expires_at: Optional[datetime] = None

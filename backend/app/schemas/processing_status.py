"""Investigation pipeline status on a persisted claim."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class StageStatus(str, Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class OverallStatus(str, Enum):
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class DocumentStageStatus(BaseModel):
    status: StageStatus = StageStatus.PENDING
    total: int = 0
    processed: int = 0
    failed: int = 0


class SimpleStageStatus(BaseModel):
    status: StageStatus = StageStatus.PENDING
    error: Optional[str] = None


class ProcessingStatus(BaseModel):
    overall: OverallStatus = OverallStatus.PROCESSING
    documents: DocumentStageStatus = Field(default_factory=DocumentStageStatus)
    nlp: SimpleStageStatus = Field(default_factory=SimpleStageStatus)
    rag: SimpleStageStatus = Field(default_factory=SimpleStageStatus)
    technical_validation: SimpleStageStatus = Field(default_factory=lambda: SimpleStageStatus(status=StageStatus.SKIPPED))
    financial_validation: SimpleStageStatus = Field(default_factory=lambda: SimpleStageStatus(status=StageStatus.SKIPPED))
    recommendation: SimpleStageStatus = Field(default_factory=lambda: SimpleStageStatus(status=StageStatus.SKIPPED))
    last_updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def touch(self) -> None:
        self.last_updated_at = datetime.now(timezone.utc)


def initial_processing_status(pending_documents: int = 0) -> ProcessingStatus:
    ps = ProcessingStatus()
    if pending_documents > 0:
        ps.documents.total = pending_documents
        ps.documents.status = StageStatus.PENDING
    else:
        ps.documents.status = StageStatus.SKIPPED
        ps.documents.total = 0
    ps.nlp.status = StageStatus.QUEUED
    ps.rag.status = StageStatus.QUEUED
    ps.technical_validation.status = StageStatus.QUEUED
    return ps

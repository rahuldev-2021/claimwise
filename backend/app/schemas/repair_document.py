from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DocumentType(str, Enum):
    TECHNICIAN_REPORT = "TECHNICIAN_REPORT"
    REPAIR_HISTORY = "REPAIR_HISTORY"
    DIAGNOSTIC_REPORT = "DIAGNOSTIC_REPORT"
    PART_REFERENCE = "PART_REFERENCE"
    LABOUR_REFERENCE = "LABOUR_REFERENCE"
    REPAIR_MANUAL = "REPAIR_MANUAL"


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    PENDING = "PENDING"


class VectorIndexStatus(str, Enum):
    """Mongo-side index state; Chroma is rebuildable from Mongo + corpus sources."""

    PENDING = "PENDING"
    INDEXED = "INDEXED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


class RepairDocument(BaseModel):
    """A document used as evidence in the RAG retrieval pipeline."""

    model_config = ConfigDict(extra="forbid")

    document_id: str
    claim_id: Optional[str] = None
    document_type: DocumentType
    title: str
    content: str
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    model_year: Optional[int] = None
    repair_category: Optional[str] = None
    part_number: Optional[str] = None
    repair_outcome: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    evidence_scope: Optional[str] = None
    org_id: Optional[str] = None
    synthetic: bool = False
    component: Optional[str] = None
    source_document_ids: Optional[str] = None
    historical_repair_id: Optional[str] = None
    content_fingerprint: Optional[str] = None
    vector_index_status: VectorIndexStatus = VectorIndexStatus.PENDING
    vector_indexed_at: Optional[datetime] = None
    vector_index_error: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(datetime.now().astimezone().tzinfo))

    @field_validator("document_id", "title")
    @classmethod
    def strip_and_reject_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Field must not be blank")
        return v

    @field_validator("content")
    @classmethod
    def reject_blank_content(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Document content must not be blank")
        return v

    @field_validator("created_at")
    @classmethod
    def ensure_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        return v

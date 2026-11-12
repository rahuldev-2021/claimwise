import re
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.repair import Repair
from app.schemas.vehicle import Vehicle


class ClaimStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    PENDING_INFORMATION = "PENDING_INFORMATION"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"


class ClaimInput(BaseModel):
    """Inbound warranty claim submitted by a dealer technician."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str
    submission_date: datetime
    vehicle: Vehicle
    customer_complaint: str
    technician_diagnosis: str
    recommended_repair: Repair
    submitted_parts_cost: Decimal = Field(ge=0)
    submitted_labour_hours: Decimal = Field(ge=0)
    currency: str = "USD"
    supporting_document_ids: list[str] = Field(default_factory=list)
    claim_status: ClaimStatus = ClaimStatus.SUBMITTED

    @field_validator("claim_id")
    @classmethod
    def strip_and_reject_blank_id(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("claim_id must not be blank")
        return v

    @field_validator("customer_complaint", "technician_diagnosis")
    @classmethod
    def reject_blank_text(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be blank")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r"^[A-Z]{3}$", v):
            raise ValueError("Currency must be a three-letter uppercase code (e.g. USD, CAD)")
        return v

    @field_validator("submission_date")
    @classmethod
    def ensure_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("submission_date must be timezone-aware (include UTC offset)")
        return v

    @field_validator("submitted_parts_cost", "submitted_labour_hours", mode="before")
    @classmethod
    def coerce_to_decimal(cls, v: object) -> Decimal:
        """Accept string or numeric input and convert to Decimal."""
        if isinstance(v, float):
            return Decimal(str(v))
        return Decimal(v) if not isinstance(v, Decimal) else v

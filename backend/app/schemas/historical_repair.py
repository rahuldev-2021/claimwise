"""Structured historical repair records with explicit field provenance."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProvenanceKind(str, Enum):
    EXPLICIT = "explicit"
    UNAVAILABLE = "unavailable"
    UNVERIFIED = "unverified"
    DERIVED = "derived"


class FieldProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provenance_kind: ProvenanceKind
    document_id: Optional[str] = None
    excerpt: Optional[str] = None
    transformation_rule: Optional[str] = None


class HistoricalRepairRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    historical_repair_id: str
    source_document_ids: list[str] = Field(default_factory=list)
    source_claim_id: Optional[str] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    model_year: Optional[int] = None
    repair_category: Optional[str] = None
    customer_complaint: Optional[str] = None
    technician_diagnosis: Optional[str] = None
    diagnostic_findings: Optional[str] = None
    dtc_codes: list[str] = Field(default_factory=list)
    verified_failure_mode: Optional[str] = None
    recommended_repair: Optional[str] = None
    actual_repair_performed: Optional[str] = None
    repair_outcome: Optional[str] = None
    parts_cost: Optional[Decimal] = None
    labour_hours: Optional[Decimal] = None
    currency: Optional[str] = None
    verification_status: str = "UNVERIFIED"
    synthetic: bool = True
    source_date: Optional[datetime] = None
    field_provenance: dict[str, FieldProvenance] = Field(default_factory=dict)

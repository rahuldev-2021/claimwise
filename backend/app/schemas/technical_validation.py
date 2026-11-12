from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TechnicalStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    QUESTIONABLE = "QUESTIONABLE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ConsistencyLevel(str, Enum):
    CONSISTENT = "CONSISTENT"
    PARTIALLY_CONSISTENT = "PARTIALLY_CONSISTENT"
    INCONSISTENT = "INCONSISTENT"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


class EvidenceSupportClass(str, Enum):
    DIRECT_SUPPORT = "DIRECT_SUPPORT"
    INDIRECT_SUPPORT = "INDIRECT_SUPPORT"
    CONTRADICTORY = "CONTRADICTORY"
    CONTEXTUAL = "CONTEXTUAL"
    INSUFFICIENT = "INSUFFICIENT"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INDETERMINATE = "INDETERMINATE"


class RepairJustificationStatus(str, Enum):
    JUSTIFIED = "JUSTIFIED"
    PARTIALLY_JUSTIFIED = "PARTIALLY_JUSTIFIED"
    NOT_SUFFICIENTLY_JUSTIFIED = "NOT_SUFFICIENTLY_JUSTIFIED"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


class MissingEvidenceScope(str, Enum):
    SUBMITTED_DIAGNOSIS = "SUBMITTED_DIAGNOSIS"
    CLAIM_UPLOAD = "CLAIM_UPLOAD"
    RETRIEVED_KNOWLEDGE = "RETRIEVED_KNOWLEDGE"
    NOT_CHECKED = "NOT_CHECKED"


class FindingSeverity(str, Enum):
    INFO = "INFO"
    REVIEW = "REVIEW"
    MATERIAL = "MATERIAL"


class FindingType(str, Enum):
    CONTRADICTION = "CONTRADICTION"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    REPAIR_SCOPE = "REPAIR_SCOPE"
    CONSISTENCY = "CONSISTENCY"
    EVIDENCE_QUALITY = "EVIDENCE_QUALITY"
    RULE = "RULE"


class EvidenceItem(BaseModel):
    """A single piece of supporting or contradicting evidence."""

    model_config = ConfigDict(extra="forbid")

    document_id: str
    relevant_excerpt: str
    evidence_type: str  # supporting | contradictory | contextual
    relevance_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Deprecated alias; use retrieval_score when present.",
    )
    chunk_id: Optional[str] = None
    title: Optional[str] = None
    document_type: Optional[str] = None
    verification_status: Optional[str] = None
    evidence_source_type: Optional[str] = None
    evidence_scope: Optional[str] = None
    source_document_ids: Optional[str] = None
    historical_repair_id: Optional[str] = None
    source_claim_id: Optional[str] = None
    assessment_reason: Optional[str] = None
    support_class: Optional[EvidenceSupportClass] = None
    retrieval_score: Optional[float] = Field(default=None, ge=0.0)
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class MissingEvidenceFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    missing_item: str
    source_scope_checked: MissingEvidenceScope
    related_component: Optional[str] = None
    related_repair_action: Optional[str] = None
    reason: str
    why_it_matters: str = ""
    suggested_evidence: str = ""
    related_rule_id: Optional[str] = None
    priority: FindingSeverity = FindingSeverity.REVIEW


class ValidationFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(default_factory=lambda: f"VF-{uuid4().hex[:12].upper()}")
    finding_type: FindingType
    description: str
    severity: FindingSeverity = FindingSeverity.REVIEW
    rule_id: Optional[str] = None
    related_claim_fields: list[str] = Field(default_factory=list)
    supporting_evidence_refs: list[str] = Field(default_factory=list)
    contradictory_evidence_refs: list[str] = Field(default_factory=list)
    explanation: str = ""
    requires_human_review: bool = True


class RepairActionAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    original_text: str
    normalized_operation: str
    component: Optional[str] = None
    associated_diagnostic_findings: list[str] = Field(default_factory=list)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradictory_evidence_ids: list[str] = Field(default_factory=list)
    justification_status: RepairJustificationStatus
    explanation: str


class TechnicalValidationResult(BaseModel):
    """Output of the technical repair validation module."""

    model_config = ConfigDict(extra="forbid")

    validation_id: str = Field(default_factory=lambda: str(uuid4()))
    claim_id: str
    pipeline_version: str = ""
    rules_version: str = ""
    schema_version: str = ""
    input_fingerprint: str = ""
    technical_status: TechnicalStatus
    diagnosis_summary: str
    repair_assessment: str
    supporting_evidence: list[EvidenceItem] = Field(default_factory=list)
    contradictory_evidence: list[EvidenceItem] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    missing_evidence_findings: list[MissingEvidenceFinding] = Field(default_factory=list)
    validation_findings: list[ValidationFinding] = Field(default_factory=list)
    repair_action_assessments: list[RepairActionAssessment] = Field(default_factory=list)
    contextual_evidence: list[EvidenceItem] = Field(default_factory=list)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    explanation: str = ""

    complaint_diagnosis_consistency: Optional[ConsistencyLevel] = None
    diagnosis_assessment: str = ""
    repair_justification: str = ""
    evidence_quality: str = ""
    confidence_level: ConfidenceLevel = ConfidenceLevel.INDETERMINATE
    validation_reasons: list[str] = Field(default_factory=list)
    triggered_rules: list[str] = Field(default_factory=list)
    human_review_required: bool = True
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def _evidence_refs_resolve(self) -> "TechnicalValidationResult":
        valid_refs = set()
        for item in (
            self.supporting_evidence
            + self.contradictory_evidence
            + self.contextual_evidence
        ):
            if item.chunk_id:
                valid_refs.add(item.chunk_id)
            if item.document_id:
                valid_refs.add(item.document_id)
        for finding in self.validation_findings:
            for ref in finding.supporting_evidence_refs + finding.contradictory_evidence_refs:
                if ref and ref not in valid_refs:
                    raise ValueError(f"finding {finding.finding_id} references unknown evidence: {ref}")
        return self

    @field_validator("validation_findings")
    @classmethod
    def _unique_finding_ids(cls, v: list[ValidationFinding]) -> list[ValidationFinding]:
        ids = [f.finding_id for f in v]
        if len(ids) != len(set(ids)):
            raise ValueError("finding_id values must be unique within a result")
        return v

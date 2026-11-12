"""Structured contextual assessment returned by LLMs (provider-independent)."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.technical_validation import RepairJustificationStatus


class EvidenceReferenceType(str, Enum):
    DIRECT = "direct"
    INDIRECT = "indirect"
    INFERENCE = "inference"
    MISSING = "missing"


class CitedEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    chunk_id: Optional[str] = None
    reference_type: EvidenceReferenceType = EvidenceReferenceType.INDIRECT
    excerpt: str = Field(max_length=500)
    relevance_note: str = ""


class TechnicalAlignment(str, Enum):
    ALIGNED = "ALIGNED"
    PARTIALLY_ALIGNED = "PARTIALLY_ALIGNED"
    MISALIGNED = "MISALIGNED"
    UNCERTAIN = "UNCERTAIN"


class WorkflowRecommendationType(str, Enum):
    PROCEED_TO_HUMAN_REVIEW = "PROCEED_TO_HUMAN_REVIEW"
    REQUEST_ADDITIONAL_EVIDENCE = "REQUEST_ADDITIONAL_EVIDENCE"
    REQUEST_FURTHER_DIAGNOSIS = "REQUEST_FURTHER_DIAGNOSIS"
    REVIEW_REPAIR_SCOPE = "REVIEW_REPAIR_SCOPE"
    REVIEW_CONTRADICTIONS = "REVIEW_CONTRADICTIONS"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


class TechnicalInterpretation(BaseModel):
    """Advisory echo of Phase 4 status — must match TV technical_status value."""

    model_config = ConfigDict(extra="forbid")

    advisory_status: str
    explanation: str = ""


class LLMRepairInterpretation(BaseModel):
    """Advisory explanation per operation; authoritative status is read-only from Phase 4."""

    model_config = ConfigDict(extra="forbid")

    normalized_operation: str
    authoritative_justification_status: RepairJustificationStatus
    advisory_explanation: str = ""
    evidence_refs: list[str] = Field(default_factory=list)


class WorkflowRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: WorkflowRecommendationType = WorkflowRecommendationType.INSUFFICIENT_INFORMATION
    reason: str = ""
    influencing_findings: list[str] = Field(default_factory=list)


class LLMAssessmentResponse(BaseModel):
    """Validated contextual assessment. Advisory only."""

    model_config = ConfigDict(extra="forbid")

    summary: str
    symptom_diagnosis_relationship: str = ""
    evidence_relevance: str = ""
    diagnostic_gaps: list[str] = Field(default_factory=list)
    contradictions_noted: list[str] = Field(default_factory=list)
    ambiguous_areas: list[str] = Field(default_factory=list)
    cited_evidence: list[CitedEvidence] = Field(default_factory=list)
    suggested_alignment: TechnicalAlignment = TechnicalAlignment.UNCERTAIN
    uncertainty_notes: str = ""
    respects_technical_validation: bool = True
    schema_version: str = "assessment_schema_v2"
    technical_interpretation: TechnicalInterpretation | None = None
    repair_interpretations: list[LLMRepairInterpretation] = Field(default_factory=list)
    workflow_recommendation: WorkflowRecommendation | None = None
    limitations: list[str] = Field(default_factory=list)


class LLMContextualAssessment(BaseModel):
    """Wrapper stored on the claim assessment response."""

    model_config = ConfigDict(extra="forbid")

    assessment: LLMAssessmentResponse
    prompt_version: str = "assessment_v2"
    schema_version: str = "assessment_schema_v2"
    advisory_only: bool = True

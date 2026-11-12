"""Internal DTOs for the technical validation pipeline."""

from dataclasses import dataclass, field

from app.modules.nlp.schemas import NLPAnalysisResult
from app.modules.rag.schemas import RetrievalResult
from app.schemas.claim import ClaimInput
from app.schemas.technical_validation import (
    ConsistencyLevel,
    EvidenceItem,
    EvidenceSupportClass,
    TechnicalStatus,
)


@dataclass
class ClassifiedEvidence:
    document_id: str
    chunk_id: str
    title: str
    document_type: str
    verification_status: str
    excerpt: str
    support_class: EvidenceSupportClass
    retrieval_score: float
    quality_score: float
    vehicle_applicable: bool = True
    evidence_source_type: str = ""
    evidence_scope: str = ""
    source_document_ids: str | None = None
    historical_repair_id: str | None = None
    source_claim_id: str | None = None
    assessment_reason: str | None = None


@dataclass
class ComplaintDiagnosisAssessment:
    consistency: ConsistencyLevel
    summary: str


@dataclass
class DiagnosisAssessment:
    summary: str
    has_direct_evidence: bool
    has_measurements_in_claim: bool


@dataclass
class RepairJustificationAssessment:
    summary: str
    heavy_vs_light_mismatch: bool


@dataclass
class ContradictionFinding:
    code: str
    message: str
    related_document_id: str = ""


@dataclass
class ValidationContext:
    claim: ClaimInput
    nlp: NLPAnalysisResult
    retrieval: RetrievalResult
    complaint_diagnosis: ComplaintDiagnosisAssessment | None = None
    diagnosis_assessment: DiagnosisAssessment | None = None
    repair_justification: RepairJustificationAssessment | None = None
    classified: list[ClassifiedEvidence] = field(default_factory=list)
    supporting: list[EvidenceItem] = field(default_factory=list)
    contradictory: list[EvidenceItem] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    contradictions: list[ContradictionFinding] = field(default_factory=list)
    validation_findings: list = field(default_factory=list)
    missing_structured: list = field(default_factory=list)
    repair_action_assessments: list = field(default_factory=list)
    triggered_rules: list[str] = field(default_factory=list)
    suggested_status: TechnicalStatus = TechnicalStatus.NEEDS_REVIEW
    validation_reasons: list[str] = field(default_factory=list)
    evidence_quality_summary: str = ""
    history_only: bool = False
    empty_retrieval: bool = False
    procedure_threshold_missing: bool = False
    human_review_required: bool = True


@dataclass
class RuleOutcome:
    rule_id: str
    message: str
    status: TechnicalStatus | None = None
    human_review: bool | None = None

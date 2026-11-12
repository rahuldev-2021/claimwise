"""Pydantic models for Phase 2/2.1 NLP pipeline outputs (v0.3.0)."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TextSourceField(str, Enum):
    CUSTOMER_COMPLAINT = "customer_complaint"
    TECHNICIAN_DIAGNOSIS = "technician_diagnosis"
    RECOMMENDED_REPAIR = "recommended_repair"


class EntityCategory(str, Enum):
    COMPONENT = "component"
    PART = "part"
    SYMPTOM = "symptom"
    DIAGNOSTIC = "diagnostic"
    DIAGNOSTIC_FINDING = "diagnostic_finding"
    REPAIR_ACTION = "repair_action"
    MEASUREMENT = "measurement"
    FAILURE_MODE = "failure_mode"
    DTC_CODE = "dtc_code"
    OPERATING_CONDITION = "operating_condition"
    LOCATION = "location"


class MissingInfoSeverity(str, Enum):
    SUGGESTION = "suggestion"
    INFO = "info"


class MatchMethod(str, Enum):
    EXACT = "exact"
    ALIAS = "alias"
    FUZZY = "fuzzy"


class ExtractionMethod(str, Enum):
    RULE_BASED = "rule_based"
    REGEX = "regex"
    TAXONOMY = "taxonomy"
    FUZZY = "fuzzy"
    SPACY_HEURISTIC = "spacy_heuristic"
    LLM = "llm"


class RelationshipPredicate(str, Enum):
    LOCATED_AT = "located_at"
    AFFECTS = "affects"
    TARGETS = "targets"
    RECOMMENDS = "recommends"


class RelationshipPolarity(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


class RelationshipCertainty(str, Enum):
    """Linguistic stance in source text — not independent technical verification."""

    REPORTED = "reported"
    SUSPECTED = "suspected"
    CONFIRMED = "confirmed"


class RepairAlignmentHintType(str, Enum):
    COMPONENT_REFERENCE_MATCH = "component_reference_match"
    SYMPTOM_NOT_REFLECTED_IN_DIAGNOSIS = "symptom_not_reflected_in_diagnosis"
    MISSING_DIAGNOSTIC_FINDING_IN_SUBMITTED_DIAGNOSIS = (
        "missing_diagnostic_finding_in_submitted_diagnosis"
    )
    DTC_PRESENT_IN_SUBMITTED_DIAGNOSIS = "dtc_present_in_submitted_diagnosis"


class ExtractedEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str = ""
    text: str
    canonical: str
    category: EntityCategory
    source_field: TextSourceField
    span_start: Optional[int] = None
    span_end: Optional[int] = None
    source_text: str = ""
    negated: bool = False
    match_method: MatchMethod = MatchMethod.ALIAS
    extraction_method: ExtractionMethod = ExtractionMethod.TAXONOMY
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    source_certainty: Optional[RelationshipCertainty] = None
    llm_reconciled: bool = False


class FieldExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_field: TextSourceField
    entities: list[ExtractedEntity] = Field(default_factory=list)
    relevant_phrases: list[str] = Field(default_factory=list)


class MissingInformationItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    severity: MissingInfoSeverity = MissingInfoSeverity.SUGGESTION


class SymptomDiagnosisPair(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symptom_canonical: str
    diagnosis_canonical: Optional[str] = None
    note: str = ""


class ComplaintDiagnosisComparison(BaseModel):
    """Review hints only. A match does not prove a repair is technically justified."""

    model_config = ConfigDict(extra="forbid")

    related_pairs: list[SymptomDiagnosisPair] = Field(default_factory=list)
    matching_components: list[str] = Field(default_factory=list)
    unrelated_components: list[str] = Field(default_factory=list)
    missing_diagnostic_support: list[str] = Field(default_factory=list)
    notes_for_reviewer: list[str] = Field(default_factory=list)


class EntityRelationship(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationship_id: str
    subject_entity_id: str
    predicate: RelationshipPredicate
    object_entity_id: str
    source_field: TextSourceField
    source_text: str
    confidence: float = Field(ge=0.0, le=1.0)
    extraction_method: ExtractionMethod = ExtractionMethod.RULE_BASED
    polarity: RelationshipPolarity = RelationshipPolarity.POSITIVE
    certainty: RelationshipCertainty = RelationshipCertainty.REPORTED


class RepairAlignmentHint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: RepairAlignmentHintType
    description: str
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    requires_validation: bool = True


class StructuredExtraction(BaseModel):
    """Shared extraction block for RAG / later offline indexing."""

    model_config = ConfigDict(extra="forbid")

    symptom: Optional[str] = None
    component: Optional[str] = None
    failure_mode: Optional[str] = None
    repair_action: Optional[str] = None
    part_number: Optional[str] = None
    dtc_codes: list[str] = Field(default_factory=list)
    operating_conditions: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)


class RecommendedRepairExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repair_category: str
    part_number: Optional[str] = None
    part_description: str
    recommended_action: str
    entities: list[ExtractedEntity] = Field(default_factory=list)


class LLMFallbackDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    considered: bool = True
    triggered: bool = False
    invoked: bool = False
    succeeded: bool = False
    trigger_codes: list[str] = Field(default_factory=list)
    min_trigger_count_met: bool = False


class LLMFallbackExecution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Optional[str] = None
    model: Optional[str] = None
    latency_ms: Optional[float] = None
    error_code: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    finish_reason: Optional[str] = None
    response_bytes: Optional[int] = None


class ReconciliationConflict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    deterministic_ref: str
    llm_ref: str
    resolution: str = "kept_deterministic"


class LLMFallbackMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    mode: str = "conditional"
    decision: LLMFallbackDecision = Field(default_factory=LLMFallbackDecision)
    execution: Optional[LLMFallbackExecution] = None
    reconciliation_conflict_count: int = 0
    conflicts: list[ReconciliationConflict] = Field(default_factory=list)


class ProcessingMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pipeline_version: str = "0.4.0"
    duration_ms: float = 0.0
    spacy_available: bool = False
    extractor_modes: list[str] = Field(default_factory=list)
    taxonomy_version: str = ""
    abbreviation_dict_version: str = ""
    fuzzy_matcher: str = "difflib"
    spacy_model: Optional[str] = None
    llm_fallback: Optional[LLMFallbackMetadata] = None


class NLPAnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    original_complaint: str
    original_diagnosis: str
    original_repair: str = ""
    normalized_complaint: str
    normalized_diagnosis: str
    normalized_repair: str = ""
    field_extractions: list[FieldExtraction] = Field(default_factory=list)
    recommended_repair: RecommendedRepairExtraction
    missing_information: list[MissingInformationItem] = Field(default_factory=list)
    complaint_diagnosis_comparison: ComplaintDiagnosisComparison
    repair_alignment_hints: list[RepairAlignmentHint] = Field(default_factory=list)
    entity_relationships: list[EntityRelationship] = Field(default_factory=list)
    structured_extraction: StructuredExtraction
    processing_metadata: ProcessingMetadata
    nlp_error: Optional[str] = None

    @model_validator(mode="after")
    def validate_relationship_entity_refs(self) -> "NLPAnalysisResult":
        ids = {
            e.entity_id
            for ext in self.field_extractions
            for e in ext.entities
            if e.entity_id
        }
        ids.update(e.entity_id for e in self.recommended_repair.entities if e.entity_id)
        for rel in self.entity_relationships:
            if rel.subject_entity_id not in ids or rel.object_entity_id not in ids:
                raise ValueError(
                    f"Relationship {rel.relationship_id} references unknown entity id"
                )
        return self

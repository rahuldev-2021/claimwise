import type { ClaimInput } from "./claim";
import type { FinancialAssessmentStatus, FinancialValidationResult } from "./financial";

export type TechnicalStatus =
  | "SUPPORTED"
  | "QUESTIONABLE"
  | "INSUFFICIENT_EVIDENCE"
  | "NEEDS_REVIEW";

export type ConsistencyLevel =
  | "CONSISTENT"
  | "PARTIALLY_CONSISTENT"
  | "INCONSISTENT"
  | "INSUFFICIENT_INFORMATION";

export type RepairJustificationStatus =
  | "JUSTIFIED"
  | "PARTIALLY_JUSTIFIED"
  | "NOT_SUFFICIENTLY_JUSTIFIED"
  | "INSUFFICIENT_INFORMATION";

export type OverallRecommendation =
  | "PROCEED_TO_HUMAN_REVIEW"
  | "PROCEED_TO_REVIEW"
  | "REQUEST_MORE_EVIDENCE"
  | "REQUEST_ADDITIONAL_EVIDENCE"
  | "REQUEST_FURTHER_DIAGNOSIS"
  | "REVIEW_REPAIR_SCOPE"
  | "REVIEW_CONTRADICTIONS"
  | "FLAG_FOR_REVIEW"
  | "INSUFFICIENT_INFORMATION";

export type LLMExecutionStatus =
  | "DISABLED"
  | "SUCCESS"
  | "FAILED"
  | "SKIPPED"
  | "FALLBACK";

export type BenchmarkPosition = "BELOW_TYPICAL" | "NEAR_TYPICAL" | "ABOVE_TYPICAL" | "UNKNOWN";

export interface FinancialDimensionBrief {
  dimension: string;
  position: BenchmarkPosition;
  submitted_value: string;
  typical_value?: string | null;
  discrepancy_pct?: string | null;
  dealer_note: string;
}

export type ClaimResponseVerdict =
  | "IN_LINE"
  | "NEEDS_REVIEW"
  | "NEEDS_DOCUMENTS"
  | "EXPLAIN_COSTS"
  | "NOT_FULLY_CHECKED";

export interface DealerClaimResponse {
  verdict: ClaimResponseVerdict;
  verdict_label: string;
  summary: string;
  because: string[];
  what_to_say: string;
}

export interface DealerCommunicationBrief {
  advisory_only: boolean;
  benchmark_source: string;
  overall_financial_position: BenchmarkPosition;
  price_discussion_suggested: boolean;
  parts?: FinancialDimensionBrief | null;
  labour?: FinancialDimensionBrief | null;
  dealer_headline: string;
  dealer_talking_points: string[];
  customer_talking_points: string[];
  technical_dealer_note: string;
  response?: DealerClaimResponse | null;
}

export interface ClaimAssessmentResponse {
  claim_id: string;
  nlp_analysis: NlpAnalysisResult;
  retrieval: RetrievalResult;
  technical_validation: TechnicalValidationResult;
  llm_contextual_assessment?: LLMContextualAssessment | null;
  llm_execution: LLMExecutionRecord;
  recommendation: ClaimRecommendation;
  execution_metadata: AssessmentExecutionMetadata;
  dealer_communication?: DealerCommunicationBrief | null;
}

export interface RetrievedPassage {
  chunk_id: string;
  document_id: string;
  title: string;
  document_type: string;
  verification_status: string;
  evidence_scope?: string;
  evidence_source_type?: string;
  text: string;
  score: number;
  rank: number;
  metadata?: Record<string, unknown>;
}

export interface RetrievalResult {
  passages: RetrievedPassage[];
  note?: string;
  query?: string;
  strategy?: string;
}

export interface EvidenceItem {
  document_id: string;
  relevant_excerpt: string;
  evidence_type: string;
  chunk_id?: string | null;
  title?: string | null;
  document_type?: string | null;
  verification_status?: string | null;
  support_class?: string | null;
  retrieval_score?: number | null;
  quality_score?: number | null;
}

export interface MissingEvidenceFinding {
  missing_item: string;
  source_scope_checked: string;
  reason: string;
  why_it_matters?: string;
  suggested_evidence?: string;
  priority?: string;
}

export interface ValidationFinding {
  finding_id: string;
  finding_type: string;
  description: string;
  severity: string;
  explanation?: string;
  requires_human_review?: boolean;
}

export interface RepairActionAssessment {
  original_text: string;
  normalized_operation: string;
  component?: string | null;
  associated_diagnostic_findings: string[];
  justification_status: RepairJustificationStatus;
  explanation: string;
}

export interface TechnicalValidationResult {
  claim_id: string;
  technical_status: TechnicalStatus;
  diagnosis_summary: string;
  repair_assessment: string;
  supporting_evidence: EvidenceItem[];
  contradictory_evidence: EvidenceItem[];
  contextual_evidence?: EvidenceItem[];
  missing_evidence: string[];
  missing_evidence_findings?: MissingEvidenceFinding[];
  validation_findings?: ValidationFinding[];
  repair_action_assessments?: RepairActionAssessment[];
  explanation: string;
  complaint_diagnosis_consistency?: ConsistencyLevel | string | null;
  diagnosis_assessment?: string;
  repair_justification?: string;
  evidence_quality?: string;
  confidence_level?: string;
  validation_reasons: string[];
  triggered_rules: string[];
  human_review_required: boolean;
  confidence?: number | null;
}

export interface CitedEvidence {
  document_id: string;
  chunk_id?: string | null;
  reference_type?: string;
  excerpt: string;
  relevance_note?: string;
}

export interface LLMAssessmentPayload {
  summary: string;
  symptom_diagnosis_relationship?: string;
  evidence_relevance?: string;
  diagnostic_gaps?: string[];
  contradictions_noted?: string[];
  ambiguous_areas?: string[];
  cited_evidence?: CitedEvidence[];
  suggested_alignment?: string;
  uncertainty_notes?: string;
  limitations?: string[];
  technical_interpretation?: { advisory_status: string; explanation: string } | null;
  repair_interpretations?: Array<{
    normalized_operation: string;
    authoritative_justification_status: RepairJustificationStatus;
    advisory_explanation: string;
  }>;
}

export interface LLMContextualAssessment {
  assessment: LLMAssessmentPayload;
  prompt_version: string;
  advisory_only: boolean;
}

export interface LLMExecutionRecord {
  status: LLMExecutionStatus;
  configured_provider?: string;
  actual_provider?: string | null;
  actual_model?: string | null;
  prompt_version?: string;
  latency_ms?: number | null;
  error_message?: string | null;
  validation_errors?: string[];
  attempt_notes?: string[];
  raw_output_preview?: string | null;
  json_repair_attempted?: boolean;
}

export interface ClaimRecommendation {
  claim_id: string;
  overall_recommendation: OverallRecommendation;
  recommendation_reasons: string[];
  evidence_document_ids: string[];
  missing_information: string[];
  human_review_required: boolean;
  triggered_business_rules: string[];
  financial_assessment_status: FinancialAssessmentStatus | string;
  financial_validation?: FinancialValidationResult | null;
  llm_advisory_summary?: string | null;
  llm_structured?: LLMAssessmentPayload | null;
  technical_validation?: TechnicalValidationResult | null;
}

export interface AssessmentExecutionMetadata {
  assessment_id: string;
  duration_ms: number;
  financial_assessment_status: FinancialAssessmentStatus | string;
  rag_mode?: string;
  generated_at?: string;
}

export interface NlpAnalysisResult {
  original_complaint?: string;
  normalized_complaint?: string;
  original_diagnosis?: string;
  normalized_diagnosis?: string;
  original_repair?: string;
  normalized_repair?: string;
  field_extractions?: Array<{
    source_field: string;
    entities: Array<{
      entity_id?: string;
      text: string;
      canonical: string;
      category: string;
      source_text?: string;
    }>;
  }>;
  missing_information?: Array<{ code: string; message: string; severity: string }>;
  complaint_diagnosis_comparison?: ComplaintDiagnosisComparison;
  repair_alignment_hints?: Array<{ type: string; description: string; requires_validation?: boolean }>;
  entity_relationships?: Array<{
    relationship_id: string;
    predicate: string;
    source_text: string;
    certainty?: string;
  }>;
  structured_extraction?: Record<string, string | null | undefined | string[]>;
  nlp_error?: string | null;
}

export interface ComplaintDiagnosisComparison {
  related_pairs?: Array<{ symptom_canonical: string; diagnosis_canonical?: string | null; note?: string }>;
  matching_components?: string[];
  unrelated_components?: string[];
  missing_diagnostic_support?: string[];
  notes_for_reviewer?: string[];
}

export interface AssessmentAnalyzeRequest {
  claim_id: string;
  top_k?: number;
  auto_ingest?: boolean;
  llm_enabled?: boolean;
  financial_enabled?: boolean;
  retrieval_mode?: "basic" | "advanced";
  force_refresh?: boolean;
}

export type { ClaimInput };

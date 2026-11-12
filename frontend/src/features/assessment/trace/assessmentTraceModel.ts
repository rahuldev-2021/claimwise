import type { ClaimAssessmentResponse } from "../../../api/types/assessment";
import type { ClaimInput } from "../../../api/types/claim";
import {
  financialAssessmentStatusLabel,
  recommendationLabel,
  technicalStatusLabel,
} from "../../../lib/statusLabels";

export type StepTone = "ok" | "warn" | "err" | "mute" | "accent";

export type AssessmentPipelineStep = {
  id: string;
  title: string;
  tone: StepTone;
  pills: string[];
  summary: string;
  detail?: string;
  isFinal?: boolean;
};

export type AssessmentTraceStats = {
  durationMs: number;
  passageCount: number;
  technicalStatus: string;
  recommendation: string;
  financialStatus: string;
  llmStatus: string;
  assessmentId: string;
  generatedAt?: string;
};

export function buildPipelineSteps(assessment: ClaimAssessmentResponse): AssessmentPipelineStep[] {
  const nlp = assessment.nlp_analysis;
  const rag = assessment.retrieval;
  const tv = assessment.technical_validation;
  const rec = assessment.recommendation;
  const llm = assessment.llm_execution;
  const finStatus = String(rec.financial_assessment_status);

  const nlpTone: StepTone = nlp.nlp_error ? "warn" : "ok";
  const ragTone: StepTone = rag.passages.length > 0 ? "ok" : rag.note ? "warn" : "mute";
  const tvTone: StepTone =
    tv.technical_status === "SUPPORTED" ? "ok" : tv.human_review_required ? "warn" : "accent";
  const finTone: StepTone =
    finStatus === "AVAILABLE" && rec.financial_validation ? "ok" : finStatus === "UNAVAILABLE" ? "mute" : "warn";
  const llmTone: StepTone =
    llm.status === "SUCCESS"
      ? "ok"
      : llm.status === "FAILED"
        ? "err"
        : llm.status === "DISABLED" || llm.status === "SKIPPED"
          ? "mute"
          : "warn";

  return [
    {
      id: "nlp",
      title: "NLP extraction",
      tone: nlpTone,
      pills: [nlp.nlp_error ? "Error recorded" : "Completed"],
      summary: nlp.normalized_complaint?.slice(0, 120) ?? "Normalized claim narrative fields.",
      detail: nlp.nlp_error ?? undefined,
    },
    {
      id: "rag",
      title: "RAG retrieval",
      tone: ragTone,
      pills: [`${rag.passages.length} passages`, rag.strategy ?? "default strategy"].filter(Boolean),
      summary: rag.query ? `Query: ${rag.query}` : rag.note ?? "Evidence passages for technical validation.",
      detail: rag.note,
    },
    {
      id: "technical",
      title: "Technical validation",
      tone: tvTone,
      pills: [
        technicalStatusLabel(tv.technical_status),
        tv.human_review_required ? "Human review" : "Automated path",
      ],
      summary: tv.explanation,
    },
    {
      id: "financial",
      title: "Financial validation",
      tone: finTone,
      pills: [financialAssessmentStatusLabel(finStatus)],
      summary: rec.financial_validation
        ? `Model status: ${rec.financial_validation.financial_status}`
        : "No ML financial output for this run.",
      detail: rec.financial_validation?.explanation?.slice(0, 500),
    },
    {
      id: "llm",
      title: "LLM advisory",
      tone: llmTone,
      pills: [llm.status, llm.actual_model ?? llm.configured_provider ?? "—"].filter((x) => x !== "—"),
      summary:
        assessment.llm_contextual_assessment?.assessment.summary ??
        rec.llm_advisory_summary ??
        llm.error_message ??
        "No LLM narrative returned.",
      detail:
        llm.status === "FAILED" && !assessment.llm_contextual_assessment
          ? "Gateway model did not return usable JSON. Technical validation and business rules remain authoritative."
          : undefined,
    },
    {
      id: "recommendation",
      title: "Workflow recommendation",
      tone: "ok",
      isFinal: true,
      pills: [recommendationLabel(rec.overall_recommendation), `${rec.triggered_business_rules.length} rules`],
      summary: rec.recommendation_reasons[0] ?? "Business-rules recommendation for reviewer workflow.",
    },
  ];
}

export function deriveTraceStats(assessment: ClaimAssessmentResponse): AssessmentTraceStats {
  const meta = assessment.execution_metadata;
  return {
    durationMs: meta.duration_ms,
    passageCount: assessment.retrieval.passages.length,
    technicalStatus: technicalStatusLabel(assessment.technical_validation.technical_status),
    recommendation: recommendationLabel(assessment.recommendation.overall_recommendation),
    financialStatus: financialAssessmentStatusLabel(String(assessment.recommendation.financial_assessment_status)),
    llmStatus: assessment.llm_execution.status,
    assessmentId: meta.assessment_id,
    generatedAt: meta.generated_at,
  };
}

export function traceSubtitle(claim: ClaimInput): string {
  return `${claim.vehicle.model_year} ${claim.vehicle.make} ${claim.vehicle.model} · ${claim.claim_id}`;
}

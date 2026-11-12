import type { ClaimAssessmentResponse } from "../../api/types/assessment";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/StateMessage";
import { financialAssessmentStatusLabel, recommendationLabel, recommendationTone } from "../../lib/statusLabels";

export function LlmRecommendationSection({ assessment }: { assessment: ClaimAssessmentResponse }) {
  const rec = assessment.recommendation;
  const llmWrap = assessment.llm_contextual_assessment;
  const llm = llmWrap?.assessment ?? rec.llm_structured;
  const exec = assessment.llm_execution;

  return (
    <div className="space-y-4">
      <Card title="Workflow recommendation (business rules)">
        <div className="mb-2 flex flex-wrap gap-2">
          <Badge tone={recommendationTone(rec.overall_recommendation)}>
            {recommendationLabel(rec.overall_recommendation)}
          </Badge>
          {rec.human_review_required ? <Badge tone="amber">Human review required</Badge> : null}
          <Badge tone="slate">
            Financial: {financialAssessmentStatusLabel(String(rec.financial_assessment_status))}
          </Badge>
        </div>
        <ul className="list-disc space-y-1 pl-5 text-[13px] text-text-muted">
          {rec.recommendation_reasons.map((r, i) => (
            <li key={`${i}-${r.slice(0, 24)}`}>{r}</li>
          ))}
        </ul>
        <p className="mt-3 text-[11px] text-text-faint">
          Produced by deterministic rules. This is not a warranty approval or rejection.
        </p>
      </Card>

      <Card title="Triggered business rules">
        <ul className="flex flex-wrap gap-2">
          {rec.triggered_business_rules.map((r) => (
            <li
              key={r}
              className="rounded-md bg-surface-raised px-2.5 py-1 font-mono text-[11px] text-text-muted ring-1 ring-border"
            >
              {r}
            </li>
          ))}
        </ul>
      </Card>

      <Card title="LLM contextual assessment (advisory)">
        {llm ? (
          <div className="space-y-3">
            <p className="text-[14px] leading-relaxed text-text">{llm.summary}</p>
            {llm.symptom_diagnosis_relationship ? (
              <p className="text-[13px] text-text-muted">
                <span className="font-medium text-text">Symptom / diagnosis: </span>
                {llm.symptom_diagnosis_relationship}
              </p>
            ) : null}
            {llm.evidence_relevance ? (
              <p className="text-[13px] text-text-muted">
                <span className="font-medium text-text">Evidence relevance: </span>
                {llm.evidence_relevance}
              </p>
            ) : null}
            {llm.uncertainty_notes ? (
              <p className="rounded-lg bg-base-deep px-3 py-2 text-[13px] text-text-muted">{llm.uncertainty_notes}</p>
            ) : null}
            {llm.limitations && llm.limitations.length > 0 ? (
              <div>
                <p className="ui-label mb-1">Limitations</p>
                <ul className="list-disc pl-5 text-[13px] text-text-muted">
                  {llm.limitations.map((l) => (
                    <li key={l.slice(0, 40)}>{l}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {llm.cited_evidence && llm.cited_evidence.length > 0 ? (
              <div>
                <p className="ui-label mb-2">Cited evidence</p>
                <ul className="space-y-2">
                  {llm.cited_evidence.map((c, i) => (
                    <li key={`${c.document_id}-${i}`} className="rounded-lg border border-border px-3 py-2 text-[13px]">
                      <div className="mb-1 flex flex-wrap gap-2">
                        <Badge tone="slate">{c.document_id}</Badge>
                        {c.reference_type ? <Badge tone="blue">{c.reference_type}</Badge> : null}
                      </div>
                      <p className="text-text-muted">{c.excerpt}</p>
                      {c.relevance_note ? (
                        <p className="mt-1 text-[11px] text-text-faint">{c.relevance_note}</p>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {llm.repair_interpretations && llm.repair_interpretations.length > 0 ? (
              <div>
                <p className="ui-label mb-2">Repair interpretations (advisory)</p>
                <ul className="space-y-2 text-[13px]">
                  {llm.repair_interpretations.map((ri) => (
                    <li key={ri.normalized_operation} className="rounded-lg bg-surface-raised px-3 py-2">
                      <span className="font-medium text-text">{ri.normalized_operation}</span>
                      <span className="text-text-faint"> · status from Phase 4: </span>
                      <span className="text-text-muted">{ri.authoritative_justification_status}</span>
                      {ri.advisory_explanation ? (
                        <p className="mt-1 text-text-muted">{ri.advisory_explanation}</p>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        ) : (
          <EmptyState
            message={`LLM unavailable or disabled (status: ${exec.status}). Deterministic assessment remains authoritative.`}
          />
        )}
        <dl className="mt-4 grid gap-2 border-t border-border pt-3 text-[11px] text-text-muted sm:grid-cols-2">
          <div>
            <dt>Execution status</dt>
            <dd>{exec.status}</dd>
          </div>
          <div>
            <dt>Provider / model</dt>
            <dd>
              {exec.actual_provider || exec.configured_provider || "—"} / {exec.actual_model || "—"}
            </dd>
          </div>
          <div>
            <dt>Prompt version</dt>
            <dd>{exec.prompt_version || llmWrap?.prompt_version || "—"}</dd>
          </div>
          <div>
            <dt>Latency (ms)</dt>
            <dd>{exec.latency_ms ?? "—"}</dd>
          </div>
        </dl>
      </Card>
    </div>
  );
}

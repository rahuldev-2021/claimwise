import type { ClaimAssessmentResponse } from "../../api/types/assessment";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/StateMessage";
import { formatScore } from "../../lib/format";
import {
  consistencyLabel,
  repairJustificationLabel,
  technicalStatusLabel,
  technicalStatusTone,
} from "../../lib/statusLabels";
import { EvidenceList } from "./EvidenceList";

export function TechnicalSection({ assessment }: { assessment: ClaimAssessmentResponse }) {
  const tv = assessment.technical_validation;
  const operations = tv.repair_action_assessments ?? [];
  const findings = tv.validation_findings ?? [];
  const missingStructured = tv.missing_evidence_findings ?? [];

  return (
    <div className="space-y-4">
      <Card title="Technical validation verdict">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <Badge tone={technicalStatusTone(tv.technical_status)}>
            {technicalStatusLabel(tv.technical_status)}
          </Badge>
          {tv.human_review_required ? <Badge tone="amber">Human review required</Badge> : null}
          {tv.confidence_level ? <Badge tone="slate">Confidence: {tv.confidence_level}</Badge> : null}
          {tv.confidence != null ? <Badge tone="slate">Score {formatScore(tv.confidence)}</Badge> : null}
        </div>
        <p className="text-[14px] leading-relaxed text-text">{tv.explanation}</p>
        <p className="mt-3 text-[11px] text-text-faint">
          Authoritative technical status for warranty review. LLM output does not override this verdict.
        </p>
      </Card>

      <Card title="Structured assessments">
        <dl className="grid gap-4 text-sm sm:grid-cols-2">
          <div className="rounded-lg bg-base-deep px-3 py-2">
            <dt className="text-[10px] font-semibold uppercase tracking-wider text-text-faint">
              Complaint / diagnosis
            </dt>
            <dd className="mt-1 font-medium text-text">
              {consistencyLabel(tv.complaint_diagnosis_consistency)}
            </dd>
          </div>
          <div className="rounded-lg bg-base-deep px-3 py-2">
            <dt className="text-[10px] font-semibold uppercase tracking-wider text-text-faint">
              Evidence quality
            </dt>
            <dd className="mt-1 text-text">{tv.evidence_quality || "—"}</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-text-faint">Diagnosis assessment</dt>
            <dd className="mt-1 text-text-muted">{tv.diagnosis_assessment || tv.diagnosis_summary}</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-text-faint">Repair justification</dt>
            <dd className="mt-1 text-text-muted">{tv.repair_justification || tv.repair_assessment}</dd>
          </div>
        </dl>
      </Card>

      {operations.length > 0 ? (
        <Card title="Repair operation justification">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-[13px]">
              <thead>
                <tr className="border-b border-border text-[10px] font-semibold uppercase tracking-wider text-text-faint">
                  <th className="py-2 pr-4">Operation</th>
                  <th className="py-2 pr-4">Component</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2">Explanation</th>
                </tr>
              </thead>
              <tbody>
                {operations.map((op) => (
                  <tr key={op.normalized_operation + op.original_text} className="border-b border-border/60">
                    <td className="py-2.5 pr-4 font-medium text-text">{op.normalized_operation}</td>
                    <td className="py-2.5 pr-4 text-text-muted">{op.component ?? "—"}</td>
                    <td className="py-2.5 pr-4">
                      <Badge
                        tone={
                          op.justification_status === "JUSTIFIED"
                            ? "green"
                            : op.justification_status === "PARTIALLY_JUSTIFIED"
                              ? "amber"
                              : "red"
                        }
                      >
                        {repairJustificationLabel(op.justification_status)}
                      </Badge>
                    </td>
                    <td className="py-2.5 text-text-muted">{op.explanation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : null}

      {findings.length > 0 ? (
        <Card title="Validation findings">
          <ul className="space-y-2">
            {findings.map((f) => (
              <li
                key={f.finding_id}
                className="rounded-lg border border-border bg-surface-raised px-3 py-2.5 text-[13px]"
              >
                <div className="mb-1 flex flex-wrap items-center gap-2">
                  <span className="font-mono text-[11px] text-text-faint">{f.finding_id}</span>
                  <Badge tone={f.severity === "MATERIAL" ? "red" : f.severity === "REVIEW" ? "amber" : "slate"}>
                    {f.finding_type}
                  </Badge>
                </div>
                <p className="font-medium text-text">{f.description}</p>
                {f.explanation ? <p className="mt-1 text-text-muted">{f.explanation}</p> : null}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {tv.supporting_evidence.length > 0 ? (
        <Card title="Supporting evidence">
          <EvidenceList items={tv.supporting_evidence} variant="supporting" />
        </Card>
      ) : null}

      {tv.contextual_evidence && tv.contextual_evidence.length > 0 ? (
        <Card title="Contextual evidence">
          <EvidenceList items={tv.contextual_evidence} variant="contextual" />
        </Card>
      ) : null}

      {tv.contradictory_evidence.length > 0 ? (
        <Card title="Contradictory evidence">
          <EvidenceList items={tv.contradictory_evidence} variant="contradictory" />
        </Card>
      ) : null}

      {missingStructured.length > 0 ? (
        <Card title="Missing evidence (structured)">
          <ul className="space-y-2 text-[13px]">
            {missingStructured.map((m) => (
              <li key={m.missing_item} className="rounded-lg border border-border px-3 py-2">
                <p className="font-medium text-text">{m.missing_item}</p>
                <p className="text-text-muted">{m.reason}</p>
                {m.suggested_evidence ? (
                  <p className="mt-1 text-[12px] text-text-faint">Suggested: {m.suggested_evidence}</p>
                ) : null}
              </li>
            ))}
          </ul>
        </Card>
      ) : tv.missing_evidence.length ? (
        <Card title="Missing evidence">
          <ul className="list-disc pl-5 text-[13px] text-text-muted">
            {tv.missing_evidence.map((m) => (
              <li key={m}>{m}</li>
            ))}
          </ul>
        </Card>
      ) : null}

      <Card title="Triggered validation rules">
        {tv.triggered_rules.length ? (
          <ul className="flex flex-wrap gap-2">
            {tv.triggered_rules.map((r) => (
              <li
                key={r}
                className="rounded-md bg-surface-raised px-2.5 py-1 font-mono text-[11px] text-text-muted ring-1 ring-border"
              >
                {r}
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState message="No rules triggered." />
        )}
      </Card>
    </div>
  );
}

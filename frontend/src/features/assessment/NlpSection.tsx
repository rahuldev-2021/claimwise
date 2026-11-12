import type { ClaimAssessmentResponse, NlpAnalysisResult } from "../../api/types/assessment";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/StateMessage";

export function NlpSection({ assessment }: { assessment: ClaimAssessmentResponse }) {
  const nlp = assessment.nlp_analysis as NlpAnalysisResult;
  const entities =
    nlp.field_extractions?.flatMap((f) =>
      f.entities.map((e) => ({ ...e, source_field: f.source_field })),
    ) ?? [];

  return (
    <div className="space-y-4">
      {nlp.nlp_error ? (
        <Card title="NLP status">
          <p className="text-sm text-amber-700">Pipeline error (claim preserved): {nlp.nlp_error}</p>
        </Card>
      ) : null}

      <Card title="Original vs normalized text">
        <dl className="space-y-3 text-sm">
          <div>
            <dt className="font-medium text-text-muted">Complaint</dt>
            <dd className="text-text-muted">Original: {nlp.original_complaint}</dd>
            <dd className="text-text">Normalized: {nlp.normalized_complaint}</dd>
          </div>
          <div>
            <dt className="font-medium text-text-muted">Diagnosis</dt>
            <dd className="text-text-muted">Original: {nlp.original_diagnosis}</dd>
            <dd className="text-text">Normalized: {nlp.normalized_diagnosis}</dd>
          </div>
          {(nlp.original_repair || nlp.normalized_repair) && (
            <div>
              <dt className="font-medium text-text-muted">Recommended repair (text)</dt>
              <dd className="text-text-muted">Original: {nlp.original_repair}</dd>
              <dd className="text-text">Normalized: {nlp.normalized_repair}</dd>
            </div>
          )}
        </dl>
      </Card>

      <Card title="Structured extraction (NLP)">
        {nlp.structured_extraction ? (
          <dl className="grid gap-2 text-[13px] sm:grid-cols-2">
            {Object.entries(nlp.structured_extraction)
              .filter(([, v]) => v && (!Array.isArray(v) || v.length > 0))
              .map(([key, value]) => (
                <div key={key}>
                  <dt className="text-text-faint">{key.replaceAll("_", " ")}</dt>
                  <dd>{Array.isArray(value) ? value.join(", ") : String(value)}</dd>
                </div>
              ))}
          </dl>
        ) : (
          <EmptyState message="No structured extraction returned." />
        )}
      </Card>

      <Card title="Extracted entities">
        {entities.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-[11px] uppercase text-text-faint">
                  <th className="py-1 pr-3">Field</th>
                  <th className="py-1 pr-3">Category</th>
                  <th className="py-1 pr-3">Text</th>
                  <th className="py-1 pr-3">Source excerpt</th>
                </tr>
              </thead>
              <tbody>
                {entities.map((e, idx) => (
                  <tr key={`${e.entity_id ?? e.canonical}-${idx}`} className="border-t border-border">
                    <td className="py-2 pr-3">{e.source_field}</td>
                    <td className="py-2 pr-3">{e.category}</td>
                    <td className="py-2 pr-3">{e.text}</td>
                    <td className="py-2 pr-3 text-text-muted">{e.source_text || e.text}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState message="No entities extracted." />
        )}
      </Card>

      {nlp.entity_relationships?.length ? (
        <Card title="Entity relationships (observations)">
          <ul className="space-y-2 text-[13px]">
            {nlp.entity_relationships.map((r) => (
              <li key={r.relationship_id} className="border-t border-border pt-2">
                <span className="font-mono text-text-faint">{r.relationship_id}</span>{" "}
                {r.predicate} — <em>{r.source_text}</em>
                {r.certainty ? ` (${r.certainty})` : ""}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {nlp.repair_alignment_hints?.length ? (
        <Card title="Repair alignment hints (requires validation)">
          <ul className="list-disc space-y-1 pl-5 text-[13px] text-text-muted">
            {nlp.repair_alignment_hints.map((h) => (
              <li key={h.type}>
                <span className="font-mono text-[11px]">{h.type}</span>: {h.description}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      <Card title="Complaint / diagnosis comparison (hints only)">
        {nlp.complaint_diagnosis_comparison ? (
          <div className="space-y-3 text-[13px]">
            {nlp.complaint_diagnosis_comparison.notes_for_reviewer &&
            nlp.complaint_diagnosis_comparison.notes_for_reviewer.length > 0 ? (
              <ul className="list-disc space-y-1 pl-5 text-text-muted">
                {nlp.complaint_diagnosis_comparison.notes_for_reviewer.map((n) => (
                  <li key={n.slice(0, 40)}>{n}</li>
                ))}
              </ul>
            ) : null}
            {nlp.complaint_diagnosis_comparison.matching_components &&
            nlp.complaint_diagnosis_comparison.matching_components.length > 0 ? (
              <div>
                <p className="ui-label">Matching components</p>
                <p className="text-text-muted">
                  {nlp.complaint_diagnosis_comparison.matching_components.join(", ")}
                </p>
              </div>
            ) : null}
            {nlp.complaint_diagnosis_comparison.unrelated_components &&
            nlp.complaint_diagnosis_comparison.unrelated_components.length > 0 ? (
              <div>
                <p className="ui-label">Unrelated components</p>
                <p className="text-text-muted">
                  {nlp.complaint_diagnosis_comparison.unrelated_components.join(", ")}
                </p>
              </div>
            ) : null}
            {nlp.complaint_diagnosis_comparison.missing_diagnostic_support &&
            nlp.complaint_diagnosis_comparison.missing_diagnostic_support.length > 0 ? (
              <div>
                <p className="ui-label">Missing diagnostic support</p>
                <ul className="list-disc pl-5 text-text-muted">
                  {nlp.complaint_diagnosis_comparison.missing_diagnostic_support.map((m) => (
                    <li key={m}>{m}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {nlp.complaint_diagnosis_comparison.related_pairs &&
            nlp.complaint_diagnosis_comparison.related_pairs.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-[12px]">
                  <thead>
                    <tr className="text-[10px] uppercase text-text-faint">
                      <th className="py-1 pr-3">Symptom</th>
                      <th className="py-1 pr-3">Diagnosis</th>
                      <th className="py-1">Note</th>
                    </tr>
                  </thead>
                  <tbody>
                    {nlp.complaint_diagnosis_comparison.related_pairs.map((p) => (
                      <tr key={`${p.symptom_canonical}-${p.diagnosis_canonical}`} className="border-t border-border">
                        <td className="py-2 pr-3">{p.symptom_canonical}</td>
                        <td className="py-2 pr-3">{p.diagnosis_canonical ?? "—"}</td>
                        <td className="py-2 text-text-muted">{p.note ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState message="No structured comparison hints." />
            )}
          </div>
        ) : (
          <EmptyState message="No comparison data." />
        )}
        <p className="mt-3 text-[11px] text-text-faint">
          Hints for reviewer alignment only—they do not prove technical justification.
        </p>
      </Card>

      {nlp.missing_information?.length ? (
        <Card title="Missing information (NLP)">
          <ul className="list-disc space-y-1 pl-5 text-[13px] text-text-muted">
            {nlp.missing_information.map((m) => (
              <li key={m.code}>
                [{m.severity}] {m.message}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}
    </div>
  );
}

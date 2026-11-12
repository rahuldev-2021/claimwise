import type { ClaimInput } from "../../api/types/claim";
import type { FinancialValidationResult } from "../../api/types/financial";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/StateMessage";
import { FinancialComparisonBars } from "../claims/FinancialComparisonBars";
import { formatMoney, formatPercent } from "../../lib/format";
import { financialAssessmentStatusLabel, financialStatusLabel, financialStatusTone } from "../../lib/statusLabels";
import { AlertTriangle, FlaskConical, Shield } from "lucide-react";

function DisclaimerBanner({ fin }: { fin: FinancialValidationResult }) {
  if (fin.synthetic_data_prediction || fin.experimental_prediction) {
    return (
      <div className="flex gap-3 rounded-lg border border-border bg-surface-raised px-4 py-3 text-[12px] text-text-muted">
        <FlaskConical className="mt-0.5 h-4 w-4 shrink-0 text-text-faint" aria-hidden />
        <div>
          <p className="font-medium text-text">Synthetic / experimental model output</p>
          <p className="mt-1 leading-relaxed">
            Predictions are for evaluation support only—not proven real-world repair costs. Human review
            is required before any warranty decision.
          </p>
          {fin.limitations ? <p className="mt-2 text-[12px] text-text-faint">{fin.limitations}</p> : null}
        </div>
      </div>
    );
  }
  return (
    <div className="flex gap-3 rounded-lg border border-border bg-surface-raised px-4 py-3 text-[12px] text-text-muted">
      <Shield className="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden />
      <p>
        Financial checks compare submitted values to model estimates. Variance flags review—it does not
        auto-approve or reject the claim.
      </p>
    </div>
  );
}

export function FinancialValidationSection({
  claim,
  financial,
  assessmentStatus,
}: {
  claim: ClaimInput;
  financial: FinancialValidationResult | null | undefined;
  assessmentStatus?: string;
}) {
  if (!financial && assessmentStatus === "PENDING") {
    return (
      <Card title="Financial validation">
        <EmptyState message="Run assessment with financial validation enabled to load predictions and discrepancy analysis." />
        <dl className="mt-4 grid gap-3 border-t border-border pt-4 text-[13px] sm:grid-cols-2">
          <div>
            <dt className="text-text-faint">Submitted parts cost</dt>
            <dd className="font-medium tabular-nums">{formatMoney(claim.submitted_parts_cost, claim.currency)}</dd>
          </div>
          <div>
            <dt className="text-text-faint">Submitted labour hours</dt>
            <dd className="font-medium tabular-nums">{claim.submitted_labour_hours} hrs</dd>
          </div>
        </dl>
      </Card>
    );
  }

  if (!financial) {
    return (
      <Card title="Financial validation">
        <div className="flex gap-2 text-[13px] text-text-muted">
          <AlertTriangle className="h-4 w-4 shrink-0 text-status-warn" />
          Financial assessment unavailable ({financialAssessmentStatusLabel(String(assessmentStatus ?? "UNAVAILABLE"))}
          ). Models may be disabled or insufficient claim features were provided.
        </div>
      </Card>
    );
  }

  const fin = financial;
  const predictedParts = fin.predicted_parts_cost != null ? Number(fin.predicted_parts_cost) : null;
  const predictedLabour = fin.predicted_labour_hours != null ? Number(fin.predicted_labour_hours) : null;

  return (
    <div className="space-y-4">
      <DisclaimerBanner fin={fin} />

      <Card title="Financial validation summary">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <Badge tone={financialStatusTone(fin.financial_status)}>
            {financialStatusLabel(fin.financial_status)}
          </Badge>
          {fin.human_review_required ? <Badge tone="amber">Human review required</Badge> : null}
          {fin.model_lifecycle ? <Badge tone="slate">Lifecycle: {fin.model_lifecycle}</Badge> : null}
        </div>

        <FinancialComparisonBars
          claim={claim}
          predictedParts={predictedParts}
          predictedLabour={predictedLabour}
        />

        <dl className="mt-6 grid gap-4 border-t border-border pt-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg bg-base-deep px-3 py-2">
            <dt className="text-[10px] font-semibold uppercase tracking-wider text-text-faint">Parts variance</dt>
            <dd className="mt-1 text-lg font-semibold tabular-nums text-text">
              {formatPercent(fin.parts_discrepancy_pct)}
            </dd>
          </div>
          <div className="rounded-lg bg-base-deep px-3 py-2">
            <dt className="text-[10px] font-semibold uppercase tracking-wider text-text-faint">Labour variance</dt>
            <dd className="mt-1 text-lg font-semibold tabular-nums text-text">
              {formatPercent(fin.labour_discrepancy_pct)}
            </dd>
          </div>
          <div className="rounded-lg bg-base-deep px-3 py-2 sm:col-span-2">
            <dt className="text-[10px] font-semibold uppercase tracking-wider text-text-faint">Explanation</dt>
            <dd className="mt-1 text-[13px] leading-relaxed text-text-muted">{fin.explanation || "—"}</dd>
          </div>
        </dl>

        {fin.triggered_financial_rules.length > 0 ? (
          <div className="mt-4 border-t border-border pt-4">
            <p className="ui-label mb-2">Triggered financial rules</p>
            <ul className="flex flex-wrap gap-2">
              {fin.triggered_financial_rules.map((r) => (
                <li
                  key={r}
                  className="rounded-md bg-surface-raised px-2.5 py-1 font-mono text-[11px] text-text-muted ring-1 ring-border"
                >
                  {r}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <dl className="mt-4 grid gap-2 border-t border-border pt-4 text-[11px] text-text-faint sm:grid-cols-2">
          <div>
            <dt>Parts model</dt>
            <dd className="text-text-muted">
              {fin.parts_model_algorithm ?? "—"}
              {fin.parts_model_version ? ` · v${fin.parts_model_version}` : ""}
            </dd>
          </div>
          <div>
            <dt>Labour model</dt>
            <dd className="text-text-muted">
              {fin.labour_model_algorithm ?? "—"}
              {fin.labour_model_version ? ` · v${fin.labour_model_version}` : ""}
            </dd>
          </div>
        </dl>
      </Card>
    </div>
  );
}

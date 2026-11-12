import type { ClaimAssessmentResponse } from "../../api/types/assessment";
import type { ClaimInput } from "../../api/types/claim";
import { Badge } from "../../components/ui/Badge";
import { formatDate, formatMoney } from "../../lib/format";
import { dealerCopy } from "../../lib/dealerCopy";
import { dealerClaimStatusLabel, dealerClaimStatusTone } from "../../lib/dealerLabels";
import { formatLabourHours } from "../../lib/dealerSummary";

export function ClaimDetailHeader({
  claim,
  assessment,
  orgName,
  compact,
}: {
  claim: ClaimInput;
  assessment: ClaimAssessmentResponse | null;
  orgName?: string | null;
  compact?: boolean;
}) {
  void assessment;

  const partsLabel = formatMoney(claim.submitted_parts_cost, claim.currency);
  const labourLabel = formatLabourHours(claim.submitted_labour_hours);

  return (
    <div
      className={
        compact
          ? "flex min-w-0 flex-1 flex-col gap-2 sm:flex-row sm:items-start sm:justify-between sm:gap-3"
          : "rounded-xl border border-border bg-surface px-4 py-3 shadow-composer"
      }
    >
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="font-mono text-lg font-bold tracking-tight text-primary sm:text-xl">{claim.claim_id}</h1>
          <Badge tone={dealerClaimStatusTone(claim.claim_status)}>{dealerClaimStatusLabel(claim.claim_status)}</Badge>
        </div>
        <p className="mt-0.5 text-[12px] text-text sm:text-[13px]">
          <span className="font-medium text-text">
            {claim.vehicle.model_year} {claim.vehicle.make} {claim.vehicle.model}
          </span>
          {claim.vehicle.vin ? (
            <span className="text-text-muted"> · {claim.vehicle.vin}</span>
          ) : (
            <span className="text-text-muted"> · No VIN</span>
          )}
        </p>
        <p className="mt-0.5 text-[11px] text-text-muted">
          {formatDate(claim.submission_date)}
          {orgName ? ` · ${orgName}` : null}
        </p>
      </div>

      <div
        className="shrink-0 rounded-lg border border-border-strong bg-surface-raised px-3 py-2 shadow-composer"
        aria-label={`${dealerCopy.sections.submittedAmounts}: ${partsLabel}, ${labourLabel}`}
      >
        <p className="text-[9px] font-bold uppercase tracking-wider text-text-muted">
          {dealerCopy.sections.submittedAmounts}
        </p>
        <p className="mt-0.5 text-xl font-bold tabular-nums leading-none text-text">{partsLabel}</p>
        <p className="mt-1 text-[13px] font-bold tabular-nums text-text-muted">{labourLabel}</p>
      </div>
    </div>
  );
}

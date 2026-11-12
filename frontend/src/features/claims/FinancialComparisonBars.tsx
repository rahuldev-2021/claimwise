import type { ClaimInput } from "../../api/types/claim";

function Bar({ label, submitted, predicted, unit }: { label: string; submitted: number; predicted?: number; unit: string }) {
  const max = Math.max(submitted, predicted ?? 0, 1);
  const subW = `${(submitted / max) * 100}%`;
  const predW = predicted != null ? `${(predicted / max) * 100}%` : "0%";

  return (
    <div className="space-y-1.5">
      <p className="text-[11px] font-medium text-text-muted">{label}</p>
      <div className="space-y-1">
        <div className="flex items-center gap-2 text-[10px] text-text-faint">
          <span className="w-16">Submitted</span>
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-base-deep">
            <div className="h-full rounded-full bg-primary/70" style={{ width: subW }} />
          </div>
          <span className="w-14 text-right tabular-nums text-text-muted">
            {submitted} {unit}
          </span>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-text-faint">
          <span className="w-16">Predicted</span>
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-base-deep">
            <div className="h-full rounded-full bg-status-ok/80" style={{ width: predW }} />
          </div>
          <span className="w-14 text-right tabular-nums text-text-muted">
            {predicted != null ? `${predicted} ${unit}` : "—"}
          </span>
        </div>
      </div>
    </div>
  );
}

export function FinancialComparisonBars({ claim, predictedParts, predictedLabour }: {
  claim: ClaimInput;
  predictedParts?: number | null;
  predictedLabour?: number | null;
}) {
  const parts = Number.parseFloat(claim.submitted_parts_cost) || 0;
  const labour = Number.parseFloat(claim.submitted_labour_hours) || 0;

  return (
    <div className="space-y-4">
      <p className="ui-label">Financial comparison</p>
      <Bar label="Parts cost" submitted={parts} predicted={predictedParts ?? undefined} unit={claim.currency} />
      <Bar label="Labour hours" submitted={labour} predicted={predictedLabour ?? undefined} unit="hrs" />
      {predictedParts == null && predictedLabour == null ? (
        <p className="text-[10px] text-text-faint">
          Predictions appear when financial validation runs and models are available on the server.
        </p>
      ) : null}
    </div>
  );
}

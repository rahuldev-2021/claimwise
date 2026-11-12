import type { ClaimStatus } from "../../api/types/claim";
import { claimStatusLabel } from "../../lib/statusLabels";

const STEPS: { id: ClaimStatus | "DRAFT" | "PROCESSING"; label: string }[] = [
  { id: "DRAFT", label: "Draft" },
  { id: "SUBMITTED", label: "Submitted" },
  { id: "UNDER_REVIEW", label: "Review" },
  { id: "PENDING_INFORMATION", label: "Info" },
  { id: "COMPLETED", label: "Decision" },
  { id: "CLOSED", label: "Closed" },
];

const ORDER = STEPS.map((s) => s.id);

function stepIndex(status: ClaimStatus): number {
  const i = ORDER.indexOf(status);
  return i >= 0 ? i : 1;
}

export function ClaimStatusStepper({ status }: { status: ClaimStatus }) {
  const active = stepIndex(status);

  return (
    <div>
      <p className="ui-label mb-3">Claim overview</p>
      <ol className="flex flex-wrap gap-1">
        {STEPS.map((step, i) => {
          const done = i <= active;
          const current = ORDER[active] === step.id;
          return (
            <li
              key={step.id}
              className={`rounded-md px-2 py-1 text-[10px] font-medium ${
                current
                  ? "bg-surface-hover text-text ring-1 ring-border-strong"
                  : done
                    ? "bg-surface-raised text-text-muted"
                    : "text-text-faint"
              }`}
            >
              {step.label}
            </li>
          );
        })}
      </ol>
      <p className="mt-2 text-[11px] text-text-faint">Current: {claimStatusLabel(status)}</p>
    </div>
  );
}

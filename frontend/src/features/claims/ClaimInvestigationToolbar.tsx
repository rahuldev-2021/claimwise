import { ChevronDown, Layers } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ClaimAssessmentResponse } from "../../api/types/assessment";
import type { ClaimInput } from "../../api/types/claim";
import { AnchoredDropdown, isAnchoredDropdownTarget } from "../../components/ui/AnchoredDropdown";
import { Button } from "../../components/ui/Button";
import { dealerCopy } from "../../lib/dealerCopy";
import { AssessmentReportDownload } from "../assessment/AssessmentReportDownload";
import { AssessmentOptionsPopover } from "./AssessmentOptionsPopover";

export function ClaimInvestigationToolbar({
  claim,
  assessment,
  canAssess = true,
  onRunAssessment,
  assessing,
  onOpenDecision,
  onOpenFullAssessment,
  canDecide = true,
  autoIngest,
  llmEnabled,
  financialEnabled,
  onAutoIngest,
  onLlmEnabled,
  onFinancialEnabled,
}: {
  claim: ClaimInput;
  assessment: ClaimAssessmentResponse | null;
  canAssess?: boolean;
  onRunAssessment: () => void;
  assessing: boolean;
  onOpenDecision: (preset?: "APPROVED" | "REJECTED" | "REQUESTED_INFO") => void;
  onOpenFullAssessment: () => void;
  canDecide?: boolean;
  autoIngest: boolean;
  llmEnabled: boolean;
  financialEnabled: boolean;
  onAutoIngest: (v: boolean) => void;
  onLlmEnabled: (v: boolean) => void;
  onFinancialEnabled: (v: boolean) => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const decisionAnchorRef = useRef<HTMLDivElement>(null);
  const decisionDisabled =
    !canDecide || claim.claim_status === "CLOSED" || claim.claim_status === "COMPLETED";

  useEffect(() => {
    if (!menuOpen) return;
    const onDoc = (e: MouseEvent) => {
      const target = e.target as Node;
      if (decisionAnchorRef.current?.contains(target)) return;
      if (isAnchoredDropdownTarget(e.target)) return;
      setMenuOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [menuOpen]);

  return (
    <div
      className={`flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-2 ${
        assessment ? "sm:justify-end" : "sm:justify-between"
      }`}
    >
      {!assessment ? (
        <span className="text-[12px] text-text-muted">Run a claim check to see repair, cost, and next step</span>
      ) : null}
      <div className="flex min-w-0 flex-wrap items-center justify-end gap-2 sm:flex-nowrap">
        <AssessmentOptionsPopover
          autoIngest={autoIngest}
          llmEnabled={llmEnabled}
          financialEnabled={financialEnabled}
          disabled={!canAssess || assessing}
          onAutoIngest={onAutoIngest}
          onLlmEnabled={onLlmEnabled}
          onFinancialEnabled={onFinancialEnabled}
        />
        <Button
          type="button"
          variant="secondary"
          className="shrink-0 whitespace-nowrap py-1.5 text-[11px]"
          onClick={onOpenFullAssessment}
          disabled={!assessment || assessing}
          title={
            assessing
              ? dealerCopy.loading.running
              : !assessment
                ? "Run a claim check first"
                : "Technical pipeline breakdown"
          }
        >
          <Layers className="mr-1.5 h-4 w-4 shrink-0" />
          {dealerCopy.actions.viewFullAssessment}
        </Button>
        <AssessmentReportDownload claim={claim} assessment={assessment} compact busy={assessing} />
        <Button
          type="button"
          variant="primary"
          className="shrink-0 whitespace-nowrap py-1.5 text-[11px]"
          onClick={onRunAssessment}
          disabled={assessing || !canAssess}
          title={!canAssess ? "Requires claims:assess" : undefined}
        >
          {assessing
            ? dealerCopy.actions.runningClaimCheck
            : assessment
              ? dealerCopy.actions.rerunClaimCheck
              : dealerCopy.actions.runClaimCheck}
        </Button>
        <div className="relative shrink-0" ref={decisionAnchorRef}>
          <Button
            type="button"
            variant="secondary"
            className="whitespace-nowrap py-1.5 text-[11px]"
            onClick={() => setMenuOpen((v) => !v)}
            disabled={decisionDisabled}
            title={decisionDisabled ? "Decision not available for this claim state" : undefined}
          >
            {dealerCopy.actions.makeDecision}
            <ChevronDown className="ml-1 h-4 w-4 shrink-0" />
          </Button>
          {!decisionDisabled ? (
            <AnchoredDropdown open={menuOpen} anchorRef={decisionAnchorRef} align="right" widthClass="w-52">
              {(
                [
                  ["Approve claim", "APPROVED"],
                  ["Reject claim", "REJECTED"],
                  ["Request more information", "REQUESTED_INFO"],
                ] as const
              ).map(([action, preset]) => (
                <button
                  key={action}
                  type="button"
                  className="block w-full px-3 py-2 text-left text-[13px] text-text-muted hover:bg-surface-hover"
                  onClick={() => {
                    setMenuOpen(false);
                    onOpenDecision(preset);
                  }}
                >
                  {action}
                </button>
              ))}
            </AnchoredDropdown>
          ) : null}
        </div>
      </div>
    </div>
  );
}

import type { ClaimAssessmentResponse } from "../../api/types/assessment";
import type { ClaimInput } from "../../api/types/claim";
import { ClaimResponseCard } from "./ClaimResponseCard";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { buildPipelineSteps } from "../assessment/trace/assessmentTraceModel";
import { formatMoney, formatPercent } from "../../lib/format";
import { dealerCopy } from "../../lib/dealerCopy";
import {
  dealerFinancialAssessmentStatusLabel,
  dealerFinancialStatusLabel,
  dealerFinancialStatusTone,
  dealerRecommendationLabel,
  dealerRecommendationTone,
  dealerTechnicalStatusLabel,
  dealerTechnicalStatusTone,
} from "../../lib/dealerLabels";
import {
  dealerCostCardLine,
  dealerNextStepLine,
  dealerRepairCardLine,
  formatLabourHours,
} from "../../lib/dealerSummary";
import { ScrollText } from "lucide-react";

function StatCard({
  label,
  badge,
  hint,
  children,
}: {
  label: string;
  badge: React.ReactNode;
  hint: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex min-h-[7.5rem] flex-col rounded-lg border border-border bg-surface px-2.5 py-2">
      <div className="flex items-start justify-between gap-2">
        <p className="text-[9px] font-bold uppercase tracking-wider text-text-muted">{label}</p>
        {badge}
      </div>
      <p className="mt-1.5 flex-1 text-[11px] leading-snug text-text">{hint}</p>
      {children ? <div className="mt-2 border-t border-border/50 pt-1.5">{children}</div> : null}
    </div>
  );
}

export function AiAnalysisWorkspace({
  claim,
  assessment,
  onShowDetails,
}: {
  claim: ClaimInput;
  assessment: ClaimAssessmentResponse;
  onShowDetails?: () => void;
}) {
  const tv = assessment.technical_validation;
  const rec = assessment.recommendation;
  const fin = rec.financial_validation;
  const llm = assessment.llm_contextual_assessment?.assessment ?? rec.llm_structured;
  const llmSummary = llm?.summary ?? rec.llm_advisory_summary ?? null;
  const stepCount = buildPipelineSteps(assessment).length;
  const currency = claim.currency || "USD";
  const claimResponse = assessment.dealer_communication?.response ?? null;

  const repairHint = dealerRepairCardLine(tv, claimResponse);
  const costHint = dealerCostCardLine(fin) ?? dealerCopy.fields.costCheckUnavailable;
  const nextHint = dealerNextStepLine(rec.overall_recommendation, claimResponse);

  return (
    <div className="space-y-2">
      {claimResponse ? <ClaimResponseCard response={claimResponse} /> : null}

      <div className="grid gap-1.5 sm:grid-cols-3">
        <StatCard
          label={dealerCopy.sections.repairCheck}
          hint={repairHint}
          badge={
            <Badge tone={dealerTechnicalStatusTone(tv.technical_status)}>
              {dealerTechnicalStatusLabel(tv.technical_status)}
            </Badge>
          }
        />

        <StatCard
          label={dealerCopy.sections.costCheck}
          hint={costHint}
          badge={
            fin ? (
              <Badge tone={dealerFinancialStatusTone(fin.financial_status)}>
                {dealerFinancialStatusLabel(fin.financial_status)}
              </Badge>
            ) : (
              <Badge tone="slate">{dealerFinancialAssessmentStatusLabel(String(rec.financial_assessment_status))}</Badge>
            )
          }
        >
          {fin ? (
            <dl className="space-y-0.5 text-[11px] text-text-muted">
              <div className="flex justify-between tabular-nums">
                <dt>Parts</dt>
                <dd className="font-semibold text-text">{formatPercent(fin.parts_discrepancy_pct)}</dd>
              </div>
              <div className="flex justify-between tabular-nums">
                <dt>Labour</dt>
                <dd className="font-semibold text-text">{formatPercent(fin.labour_discrepancy_pct)}</dd>
              </div>
              {(fin.predicted_parts_cost != null || fin.predicted_labour_hours != null) && (
                <div className="border-t border-border/50 pt-1 text-[10px] text-text-muted">
                  {fin.predicted_parts_cost != null ? (
                    <div className="flex justify-between">
                      <span>Typical parts</span>
                      <span className="font-medium text-text">{formatMoney(String(fin.predicted_parts_cost), currency)}</span>
                    </div>
                  ) : null}
                  {fin.predicted_labour_hours != null ? (
                    <div className="flex justify-between">
                      <span>Typical labour</span>
                      <span className="font-medium text-text">{formatLabourHours(fin.predicted_labour_hours)}</span>
                    </div>
                  ) : null}
                </div>
              )}
            </dl>
          ) : null}
        </StatCard>

        <StatCard
          label={dealerCopy.sections.nextStep}
          hint={nextHint}
          badge={
            <Badge tone={dealerRecommendationTone(rec.overall_recommendation)}>
              {dealerRecommendationLabel(rec.overall_recommendation)}
            </Badge>
          }
        />
      </div>

      {llmSummary && !claimResponse ? (
        <div className="rounded-lg border border-border bg-surface px-2.5 py-2">
          <p className="text-[9px] font-bold uppercase tracking-wider text-text-muted">
            {dealerCopy.sections.plainSummary}
          </p>
          <p className="mt-1 text-[12px] leading-snug text-text-muted">{llmSummary}</p>
        </div>
      ) : null}

      {onShowDetails ? (
        <div className="flex flex-wrap items-center gap-2 border-t border-border/60 pt-2">
          <Button type="button" variant="secondary" className="py-1.5 text-[11px]" onClick={onShowDetails}>
            <ScrollText className="mr-1 h-3.5 w-3.5" />
            {dealerCopy.actions.viewFullAssessment}
          </Button>
          <button
            type="button"
            onClick={onShowDetails}
            className="text-[10px] text-text-muted hover:text-accent hover:underline"
          >
            {dealerCopy.actions.openFullTrace(stepCount)}
          </button>
        </div>
      ) : null}
    </div>
  );
}

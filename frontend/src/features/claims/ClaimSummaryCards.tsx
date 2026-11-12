import type { ClaimAssessmentResponse } from "../../api/types/assessment";
import type { ClaimInput } from "../../api/types/claim";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { formatMoney } from "../../lib/format";
import { dealerCopy } from "../../lib/dealerCopy";
import {
  dealerClaimStatusLabel,
  dealerFinancialStatusLabel,
  dealerFinancialStatusTone,
  dealerRecommendationLabel,
  dealerRecommendationTone,
  dealerTechnicalStatusLabel,
  dealerTechnicalStatusTone,
} from "../../lib/dealerLabels";

export function ClaimSummaryCards({
  claim,
  assessment,
  dealerLabel,
}: {
  claim: ClaimInput;
  assessment: ClaimAssessmentResponse | null;
  dealerLabel?: string;
}) {
  const rec = assessment?.recommendation.overall_recommendation;
  const tv = assessment?.technical_validation;
  const fin = assessment?.recommendation.financial_validation;

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      <Card className="p-4">
        <p className="ui-label">Vehicle</p>
        <p className="mt-1 text-[13px] font-medium text-text">
          {claim.vehicle.model_year} {claim.vehicle.make} {claim.vehicle.model}
        </p>
        <p className="mt-1 truncate text-[11px] text-text-faint">{claim.vehicle.vin ?? "VIN not on file"}</p>
      </Card>
      <Card className="p-4">
        <p className="ui-label">Dealer</p>
        <p className="mt-1 text-[13px] font-medium text-text">{dealerLabel ?? "Authorized dealer"}</p>
        <p className="mt-1 text-[11px] text-text-faint">From your submission</p>
      </Card>
      <Card className="p-4">
        <p className="ui-label">Submitted cost</p>
        <p className="mt-1 text-lg font-semibold text-text">
          {formatMoney(claim.submitted_parts_cost, claim.currency)}
        </p>
        <p className="text-[11px] text-text-muted">{claim.submitted_labour_hours} labour hrs</p>
      </Card>
      <Card className="p-4">
        <p className="ui-label">{dealerCopy.sections.repairCheck}</p>
        <div className="mt-2">
          {tv ? (
            <Badge tone={dealerTechnicalStatusTone(tv.technical_status)}>
              {dealerTechnicalStatusLabel(tv.technical_status)}
            </Badge>
          ) : (
            <p className="text-[13px] text-text-muted">Not checked yet</p>
          )}
        </div>
      </Card>
      <Card className="p-4">
        <p className="ui-label">{dealerCopy.sections.nextStep}</p>
        <div className="mt-2">
          {rec ? (
            <Badge tone={dealerRecommendationTone(rec)}>{dealerRecommendationLabel(rec)}</Badge>
          ) : (
            <p className="text-[13px] text-text-muted">{dealerCopy.actions.runClaimCheck}</p>
          )}
        </div>
        {fin ? (
          <p className="mt-2">
            <Badge tone={dealerFinancialStatusTone(fin.financial_status)}>
              {dealerFinancialStatusLabel(fin.financial_status)}
            </Badge>
          </p>
        ) : (
          <p className="mt-2 text-[11px] text-text-faint">Status: {dealerClaimStatusLabel(claim.claim_status)}</p>
        )}
      </Card>
    </div>
  );
}

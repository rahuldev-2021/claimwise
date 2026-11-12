import type { ClaimInput } from "../../api/types/claim";
import { Card } from "../../components/ui/Card";
import { formatMoney } from "../../lib/format";

export function OverviewSection({ claim }: { claim: ClaimInput }) {
  return (
    <div className="space-y-4">
      <Card title="Customer complaint (source)">
        <p className="whitespace-pre-wrap text-[13px] text-text">{claim.customer_complaint}</p>
      </Card>
      <Card title="Technician diagnosis (source)">
        <p className="whitespace-pre-wrap text-[13px] text-text">{claim.technician_diagnosis}</p>
      </Card>
      <Card title="Recommended repair (source)">
        <dl className="grid gap-2 text-[13px] sm:grid-cols-2">
          <div>
            <dt className="text-text-faint">Category</dt>
            <dd>{claim.recommended_repair.repair_category}</dd>
          </div>
          <div>
            <dt className="text-text-faint">Part</dt>
            <dd>{claim.recommended_repair.part_description}</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-text-faint">Action</dt>
            <dd>{claim.recommended_repair.recommended_action}</dd>
          </div>
        </dl>
      </Card>
      <Card title="Submitted financial information">
        <p className="mb-2 text-[11px] text-text-faint">
          Dealer-submitted values. ML validation appears in the Financial section after assessment.
        </p>
        <dl className="grid gap-2 text-[13px] sm:grid-cols-2">
          <div>
            <dt className="text-text-faint">Parts cost</dt>
            <dd>{formatMoney(claim.submitted_parts_cost, claim.currency)}</dd>
          </div>
          <div>
            <dt className="text-text-faint">Labour hours</dt>
            <dd>{claim.submitted_labour_hours}</dd>
          </div>
        </dl>
      </Card>
    </div>
  );
}

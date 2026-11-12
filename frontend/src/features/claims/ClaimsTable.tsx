import { Link } from "react-router-dom";
import type { ClaimInput } from "../../api/types/claim";
import { Badge } from "../../components/ui/Badge";
import { formatDate } from "../../lib/format";
import { dealerCopy } from "../../lib/dealerCopy";
import { dealerClaimStatusLabel, dealerClaimStatusTone } from "../../lib/dealerLabels";

function ClaimsTableHeader() {
  return (
    <div className="border-b border-border bg-base-deep/30 px-3 py-2">
      <p className="text-[12px] font-semibold text-text">{dealerCopy.list.tableHeading}</p>
      <p className="mt-0.5 text-[11px] leading-snug text-text-muted">{dealerCopy.list.tableCaption}</p>
    </div>
  );
}

export function ClaimsTable({ claims }: { claims: ClaimInput[] }) {
  if (!claims.length) {
    return (
      <div>
        <ClaimsTableHeader />
        <div className="flex flex-col items-center justify-center px-4 py-8 text-center">
          <p className="text-[13px] font-medium text-text">No claims found</p>
          <p className="mt-1 max-w-sm text-[12px] text-text-muted">
            Adjust filters or submit a new claim to get started.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <ClaimsTableHeader />
      <table className="min-w-full text-left text-[12px]">
        <thead>
          <tr className="border-b border-border bg-surface-raised/60">
            <th className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-text-faint">
              Claim
            </th>
            <th className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-text-faint">
              Vehicle
            </th>
            <th className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-text-faint">
              Category
            </th>
            <th className="hidden px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-text-faint sm:table-cell">
              Submitted
            </th>
            <th className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-text-faint">
              Status
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {claims.map((claim) => (
            <tr key={claim.claim_id} className="transition-colors hover:bg-surface-hover/40">
              <td className="whitespace-nowrap px-3 py-2">
                <Link
                  to={`/claims/${claim.claim_id}`}
                  className="font-semibold tabular-nums text-primary hover:text-primary-hover hover:underline"
                >
                  {claim.claim_id}
                </Link>
              </td>
              <td className="px-3 py-2 text-text-muted">
                {claim.vehicle.model_year} {claim.vehicle.make} {claim.vehicle.model}
              </td>
              <td className="px-3 py-2">
                <span className="text-[10px] font-semibold uppercase tracking-wide text-text-muted">
                  {claim.recommended_repair.repair_category}
                </span>
              </td>
              <td className="hidden whitespace-nowrap px-3 py-2 text-[11px] text-text-muted sm:table-cell">
                {formatDate(claim.submission_date)}
              </td>
              <td className="px-3 py-2">
                <Badge tone={dealerClaimStatusTone(claim.claim_status)}>
                  {dealerClaimStatusLabel(claim.claim_status)}
                </Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

import type {
  DealerClaimResponse,
  OverallRecommendation,
  TechnicalStatus,
  TechnicalValidationResult,
} from "../api/types/assessment";

const REPAIR_ONE_LINERS: Record<TechnicalStatus, string> = {
  SUPPORTED: "Repair story and paperwork look aligned.",
  QUESTIONABLE: "Some details need clarification before review.",
  INSUFFICIENT_EVIDENCE: "Add photos, tests, or documents that support the repair.",
  NEEDS_REVIEW: "A reviewer will look at this claim more closely.",
};

const NEXT_STEP_ONE_LINERS: Partial<Record<OverallRecommendation, string>> = {
  FLAG_FOR_REVIEW: "Have parts and labour breakdowns ready for the reviewer.",
  PROCEED_TO_HUMAN_REVIEW: "No extra action from you right now — wait for review.",
  PROCEED_TO_REVIEW: "No extra action from you right now — wait for review.",
  REQUEST_ADDITIONAL_EVIDENCE: "Send the missing documents, then run the check again.",
  REQUEST_MORE_EVIDENCE: "Send the missing documents, then run the check again.",
  REQUEST_FURTHER_DIAGNOSIS: "Capture updated diagnosis notes before resubmitting.",
  REVIEW_REPAIR_SCOPE: "Confirm every repair line matches what was done on the vehicle.",
  REVIEW_CONTRADICTIONS: "Reconcile complaint vs diagnosis before the reviewer calls.",
  INSUFFICIENT_INFORMATION: "Fill in missing claim fields and run the check again.",
};

const VERDICT_NEXT_LINE: Record<string, string> = {
  EXPLAIN_COSTS: "Walk through parts and labour with the customer — keep invoices handy.",
  IN_LINE: "The claim fits a typical job; approval is still pending.",
  NEEDS_DOCUMENTS: "List what’s missing and ask the dealer/customer to bring it in.",
  NEEDS_REVIEW: "Don’t promise an outcome until review finishes.",
  NOT_FULLY_CHECKED: "Run the full claim check (including costs) before you quote the customer.",
};

/** Dealer-facing repair blurb — hides raw technical_status boilerplate. */
export function dealerRepairOneLiner(tv: TechnicalValidationResult): string {
  const raw = (tv.diagnosis_summary || tv.explanation || "").trim();
  const looksTechnical =
    /^technical status:/i.test(raw) ||
    /\bSUPPORTED\b/.test(raw) ||
    /attested on the claim/i.test(raw) ||
    /dealer-submitted/i.test(raw);

  if (looksTechnical || raw.length > 160) {
    return REPAIR_ONE_LINERS[tv.technical_status] ?? "See full assessment for technical detail.";
  }
  return raw.length > 140 ? `${raw.slice(0, 137)}…` : raw;
}

export function dealerRepairCardLine(
  tv: TechnicalValidationResult,
  response: DealerClaimResponse | null | undefined,
): string {
  if (tv.technical_status === "SUPPORTED") {
    if (response?.verdict === "EXPLAIN_COSTS") {
      return "Repair looks fine; focus on explaining the costs.";
    } 
    if (response?.verdict === "IN_LINE") {
      return "Repair and costs look good for this type of job.";
    }
    return "Documentation supports the repair and costs.";
  }
  return dealerRepairOneLiner(tv);
}

export function dealerNextStepLine(
  recommendation: OverallRecommendation,
  response: DealerClaimResponse | null | undefined,
): string {
  if (response?.verdict && VERDICT_NEXT_LINE[response.verdict]) {
    return VERDICT_NEXT_LINE[response.verdict];
  }
  return (
    NEXT_STEP_ONE_LINERS[recommendation] ??
    "Share clear repair details with the customer and wait for review."
  );
}

export function dealerCostCardLine(
  fin: { parts_discrepancy_pct?: string | null; labour_discrepancy_pct?: string | null } | null | undefined,
): string | null {
  if (!fin) return null;
  const parts = fin.parts_discrepancy_pct != null ? Number.parseFloat(String(fin.parts_discrepancy_pct)) : NaN;
  const labour = fin.labour_discrepancy_pct != null ? Number.parseFloat(String(fin.labour_discrepancy_pct)) : NaN;
  const highParts = !Number.isNaN(parts) && parts > 15;
  const highLabour = !Number.isNaN(labour) && labour > 15;
  if (highParts && highLabour) return "Both parts and labour are above typical — expect questions.";
  if (highParts) return "Parts are above typical — explain part numbers and pricing.";
  if (highLabour) return "Labour hours are above typical — explain time on the job.";
  if (!Number.isNaN(parts) && !Number.isNaN(labour) && Math.abs(parts) <= 15 && Math.abs(labour) <= 15) {
    return "Amounts are close to what we usually see.";
  }
  return "Compare your line items to the typical values below.";
}

export function formatLabourHours(value: string | number | null | undefined): string {
  if (value == null || value === "") return "—";
  const n = typeof value === "string" ? Number.parseFloat(value) : value;
  if (Number.isNaN(n)) return String(value);
  const rounded = Math.round(n * 10) / 10;
  return `${rounded} hrs`;
}

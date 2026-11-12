import type {
  BenchmarkPosition,
  ClaimResponseVerdict,
  OverallRecommendation,
  TechnicalStatus,
} from "../api/types/assessment";
import type { ClaimStatus } from "../api/types/claim";
import type { FinancialAssessmentStatus, FinancialStatus } from "../api/types/financial";
import {
  financialStatusTone,
  recommendationTone,
  technicalStatusTone,
  claimStatusTone,
} from "./statusLabels";

export function dealerTechnicalStatusLabel(status: TechnicalStatus): string {
  const map: Record<TechnicalStatus, string> = {
    SUPPORTED: "Looks good",
    QUESTIONABLE: "Needs clarification",
    INSUFFICIENT_EVIDENCE: "More proof needed",
    NEEDS_REVIEW: "Claim needs review",
  };
  return map[status] ?? status;
}

export function dealerFinancialStatusLabel(status: FinancialStatus): string {
  const map: Record<FinancialStatus, string> = {
    WITHIN_EXPECTED_RANGE: "In line with typical",
    OUTSIDE_EXPECTED_RANGE: "Higher or lower than usual",
    INSUFFICIENT_DATA: "Not enough info to compare",
    NEEDS_REVIEW: "Costs need a second look",
  };
  return map[status] ?? status;
}

export function dealerFinancialAssessmentStatusLabel(status: string): string {
  const map: Record<FinancialAssessmentStatus, string> = {
    PENDING: "Not checked yet",
    AVAILABLE: "Cost check done",
    UNAVAILABLE: "Cost check unavailable",
  };
  return map[status as FinancialAssessmentStatus] ?? status;
}

export function dealerRecommendationLabel(rec: OverallRecommendation): string {
  const map: Record<string, string> = {
    PROCEED_TO_HUMAN_REVIEW: "Ready for claim review",
    PROCEED_TO_REVIEW: "Ready for claim review",
    REQUEST_MORE_EVIDENCE: "Send more documents",
    REQUEST_ADDITIONAL_EVIDENCE: "Send more documents",
    REQUEST_FURTHER_DIAGNOSIS: "More diagnosis needed",
    REVIEW_REPAIR_SCOPE: "Confirm what was repaired",
    REVIEW_CONTRADICTIONS: "Stories don't match — review",
    FLAG_FOR_REVIEW: "Flag this claim",
    INSUFFICIENT_INFORMATION: "Missing details",
  };
  return map[rec] ?? rec.replaceAll("_", " ").toLowerCase();
}

export function dealerClaimStatusLabel(status: ClaimStatus): string {
  const map: Record<ClaimStatus, string> = {
    SUBMITTED: "Submitted",
    UNDER_REVIEW: "Claim in review",
    PENDING_INFORMATION: "Waiting on you",
    COMPLETED: "Approved",
    CLOSED: "Denied",
  };
  return map[status] ?? status;
}

export function dealerClaimResponseVerdictTone(
  verdict: ClaimResponseVerdict,
): "green" | "amber" | "red" | "slate" {
  switch (verdict) {
    case "IN_LINE":
      return "green";
    case "EXPLAIN_COSTS":
    case "NEEDS_REVIEW":
      return "amber";
    case "NEEDS_DOCUMENTS":
      return "red";
    default:
      return "slate";
  }
}

export function dealerBenchmarkPositionLabel(position: BenchmarkPosition | string | undefined): string {
  switch (position) {
    case "NEAR_TYPICAL":
      return "Near typical";
    case "BELOW_TYPICAL":
      return "Below typical";
    case "ABOVE_TYPICAL":
      return "Above typical";
    default:
      return "Not compared";
  }
}

export function dealerRecommendationReason(reason: string): string {
  const trimmed = reason.trim();
  const patterns: Array<[RegExp, string]> = [
    [/technical validation supports/i, "The repair story is supported — a person still makes the final call."],
    [/outside PROVISIONAL expected/i, "Parts or labour look unusual compared to typical jobs."],
    [/within PROVISIONAL expected/i, "Costs look in line with typical for this repair."],
    [/Financial validation status/i, "The cost check needs attention before moving on."],
    [/Financial ML predictions unavailable/i, "We couldn't compare costs automatically — don't assume pricing is fine."],
    [/Critical diagnostic or evidence gaps/i, "Some documents or test results are still missing."],
    [/Contradictions or review flags/i, "Something in the file doesn't line up — the claim needs a closer look."],
    [/LLM contextual reasoning unavailable/i, "Written summary wasn't available; other checks still ran."],
    [/Contextual LLM reasoning unavailable/i, "Written summary wasn't available; other checks still ran."],
    [/Insufficient information to complete/i, "There isn't enough information to finish the check yet."],
  ];
  for (const [re, replacement] of patterns) {
    if (re.test(trimmed)) return replacement;
  }
  return trimmed;
}

export {
  technicalStatusTone as dealerTechnicalStatusTone,
  financialStatusTone as dealerFinancialStatusTone,
  recommendationTone as dealerRecommendationTone,
  claimStatusTone as dealerClaimStatusTone,
};

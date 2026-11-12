import type { ConsistencyLevel, OverallRecommendation, TechnicalStatus } from "../api/types/assessment";
import type { FinancialAssessmentStatus, FinancialStatus } from "../api/types/financial";
import type { ClaimStatus } from "../api/types/claim";

export function technicalStatusLabel(status: TechnicalStatus): string {
  const map: Record<TechnicalStatus, string> = {
    SUPPORTED: "Supported",
    QUESTIONABLE: "Questionable",
    INSUFFICIENT_EVIDENCE: "Insufficient evidence",
    NEEDS_REVIEW: "Needs review",
  };
  return map[status] ?? status;
}

export function recommendationLabel(rec: OverallRecommendation): string {
  const map: Record<string, string> = {
    PROCEED_TO_HUMAN_REVIEW: "Proceed to human review",
    PROCEED_TO_REVIEW: "Proceed to human review",
    REQUEST_MORE_EVIDENCE: "Request more evidence",
    REQUEST_ADDITIONAL_EVIDENCE: "Request additional evidence",
    REQUEST_FURTHER_DIAGNOSIS: "Request further diagnosis",
    REVIEW_REPAIR_SCOPE: "Review repair scope",
    REVIEW_CONTRADICTIONS: "Review contradictions",
    FLAG_FOR_REVIEW: "Flag for review",
    INSUFFICIENT_INFORMATION: "Insufficient information",
  };
  return map[rec] ?? rec.replaceAll("_", " ").toLowerCase();
}

export function consistencyLabel(level: ConsistencyLevel | string | null | undefined): string {
  const map: Record<string, string> = {
    CONSISTENT: "Consistent",
    PARTIALLY_CONSISTENT: "Partially consistent",
    INCONSISTENT: "Inconsistent",
    INSUFFICIENT_INFORMATION: "Insufficient information",
  };
  return level ? map[level] ?? String(level) : "—";
}

export function financialStatusLabel(status: FinancialStatus): string {
  const map: Record<FinancialStatus, string> = {
    WITHIN_EXPECTED_RANGE: "Within expected range",
    OUTSIDE_EXPECTED_RANGE: "Outside expected range",
    INSUFFICIENT_DATA: "Insufficient data",
    NEEDS_REVIEW: "Needs review",
  };
  return map[status] ?? status;
}

export function financialStatusTone(
  status: FinancialStatus,
): "green" | "amber" | "red" | "slate" {
  switch (status) {
    case "WITHIN_EXPECTED_RANGE":
      return "green";
    case "OUTSIDE_EXPECTED_RANGE":
      return "red";
    case "NEEDS_REVIEW":
      return "amber";
    default:
      return "slate";
  }
}

export function financialAssessmentStatusLabel(status: string): string {
  const map: Record<FinancialAssessmentStatus, string> = {
    PENDING: "Pending",
    AVAILABLE: "Available",
    UNAVAILABLE: "Unavailable",
  };
  return map[status as FinancialAssessmentStatus] ?? status;
}

export function repairJustificationLabel(status: string): string {
  return status.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

export function claimStatusLabel(status: ClaimStatus): string {
  return status.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

export function claimStatusTone(
  status: ClaimStatus,
): "green" | "amber" | "red" | "blue" | "slate" {
  switch (status) {
    case "COMPLETED":
    case "CLOSED":
      return "green";
    case "UNDER_REVIEW":
      return "amber";
    case "PENDING_INFORMATION":
      return "red";
    case "SUBMITTED":
      return "blue";
    default:
      return "slate";
  }
}

export function technicalStatusTone(
  status: TechnicalStatus,
): "green" | "amber" | "red" | "slate" {
  switch (status) {
    case "SUPPORTED":
      return "green";
    case "QUESTIONABLE":
      return "amber";
    case "INSUFFICIENT_EVIDENCE":
      return "slate";
    case "NEEDS_REVIEW":
      return "red";
    default:
      return "slate";
  }
}

export function recommendationTone(
  rec: OverallRecommendation,
): "green" | "amber" | "red" | "slate" {
  switch (rec) {
    case "PROCEED_TO_HUMAN_REVIEW":
    case "PROCEED_TO_REVIEW":
      return "green";
    case "REQUEST_MORE_EVIDENCE":
      return "amber";
    case "FLAG_FOR_REVIEW":
      return "red";
    case "INSUFFICIENT_INFORMATION":
      return "slate";
    default:
      return "slate";
  }
}

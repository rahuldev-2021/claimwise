import { describe, expect, it } from "vitest";
import type { OverallRecommendation, TechnicalStatus } from "../api/types/assessment";
import type { FinancialStatus } from "../api/types/financial";
import {
  dealerFinancialStatusLabel,
  dealerRecommendationLabel,
  dealerRecommendationReason,
  dealerTechnicalStatusLabel,
} from "../lib/dealerLabels";
import { formatLabourHours } from "../lib/dealerSummary";

const technicalStatuses: TechnicalStatus[] = [
  "SUPPORTED",
  "QUESTIONABLE",
  "INSUFFICIENT_EVIDENCE",
  "NEEDS_REVIEW",
];

const financialStatuses: FinancialStatus[] = [
  "WITHIN_EXPECTED_RANGE",
  "OUTSIDE_EXPECTED_RANGE",
  "INSUFFICIENT_DATA",
  "NEEDS_REVIEW",
];

const recommendations: OverallRecommendation[] = [
  "PROCEED_TO_HUMAN_REVIEW",
  "REQUEST_ADDITIONAL_EVIDENCE",
  "FLAG_FOR_REVIEW",
  "INSUFFICIENT_INFORMATION",
];

describe("dealerLabels", () => {
  it("maps technical statuses without raw enum text", () => {
    for (const status of technicalStatuses) {
      const label = dealerTechnicalStatusLabel(status);
      expect(label).not.toContain("_");
      expect(label).not.toBe(status);
    }
  });

  it("maps financial statuses without raw enum text", () => {
    for (const status of financialStatuses) {
      const label = dealerFinancialStatusLabel(status);
      expect(label).not.toContain("_");
      expect(label).not.toBe(status);
    }
  });

  it("maps workflow recommendations without raw enum text", () => {
    for (const rec of recommendations) {
      const label = dealerRecommendationLabel(rec);
      expect(label).not.toContain("PROCEED_TO");
      expect(label).not.toBe(rec);
    }
  });

  it("formats labour hours to one decimal", () => {
    expect(formatLabourHours("3.422307229530359")).toBe("3.4 hrs");
    expect(formatLabourHours(7)).toBe("7 hrs");
  });

  it("softens known backend reason lines", () => {
    const out = dealerRecommendationReason(
      "Submitted costs or labour are outside PROVISIONAL expected range — additional human review.",
    );
    expect(out.toLowerCase()).toContain("unusual");
  });
});

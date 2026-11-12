import { render, screen } from "@testing-library/react";
import type { ClaimAssessmentResponse } from "../api/types/assessment";
import fixture from "./fixtures/assessment-clm-002.min.json";
import { TechnicalSection } from "../features/assessment/TechnicalSection";

describe("TechnicalSection", () => {
  it("renders backend technical status label", () => {
    render(
      <TechnicalSection assessment={fixture as unknown as ClaimAssessmentResponse} />,
    );
    expect(screen.getByText("Questionable")).toBeInTheDocument();
    expect(screen.getByText(/Review recommended/)).toBeInTheDocument();
  });
});

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DashboardPage } from "../pages/DashboardPage";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("DashboardPage", () => {
  it("renders overview when claims load", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        statusText: "OK",
        text: async () =>
          JSON.stringify([
            {
              claim_id: "CLM-002",
              submission_date: "2026-01-01T00:00:00Z",
              vehicle: {
                vehicle_id: "VH-1",
                make: "Ford",
                model: "F-150",
                model_year: 2023,
              },
              customer_complaint: "noise",
              technician_diagnosis: "pads",
              recommended_repair: {
                repair_category: "BRAKING",
                part_description: "pads",
                recommended_action: "replace",
              },
              submitted_parts_cost: "100",
              submitted_labour_hours: "1",
              currency: "USD",
              supporting_document_ids: [],
              claim_status: "UNDER_REVIEW",
            },
          ]),
      }),
    );

    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <DashboardPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    await waitFor(() => expect(screen.getByText("Overview")).toBeInTheDocument());
    expect(screen.getByText("CLM-002")).toBeInTheDocument();
  });
});

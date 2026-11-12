import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "../api/client";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiFetch", () => {
  it("throws ApiError on non-OK responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        statusText: "Not Found",
        text: async () => JSON.stringify({ detail: "Claim not found" }),
      }),
    );
    await expect(apiFetch("/api/v1/claims/NO-SUCH")).rejects.toBeInstanceOf(ApiError);
  });
});

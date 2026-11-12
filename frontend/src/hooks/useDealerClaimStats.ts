import { useQuery } from "@tanstack/react-query";
import { listClaims } from "../api/services";

export function useDealerClaimStats(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ["claims", "dealer-stats"],
    queryFn: async () => {
      const claims = await listClaims({ sort: "submission_date_desc" });
      return {
        total: claims.length,
        underReview: claims.filter((c) => c.claim_status === "UNDER_REVIEW").length,
        actionRequired: claims.filter((c) => c.claim_status === "PENDING_INFORMATION").length,
        submitted: claims.filter((c) => c.claim_status === "SUBMITTED").length,
      };
    },
    staleTime: 60_000,
    enabled: options?.enabled !== false,
  });
}

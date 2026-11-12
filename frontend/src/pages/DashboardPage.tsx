import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { listClaims } from "../api/services";
import { ClaimsTable } from "../features/claims/ClaimsTable";
import { Card } from "../components/ui/Card";
import { ErrorState, LoadingState } from "../components/ui/StateMessage";
import { countRecommendations, getCachedAssessmentSummaries } from "../lib/assessmentCache";

export function DashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["claims", "dashboard"],
    queryFn: () => listClaims({ sort: "submission_date_desc" }),
  });

  const stats = useMemo(() => {
    const claims = data ?? [];
    const session = getCachedAssessmentSummaries();
    return {
      total: claims.length,
      awaiting: claims.filter((c) => c.claim_status === "SUBMITTED" || c.claim_status === "UNDER_REVIEW").length,
      pendingInfo: claims.filter((c) => c.claim_status === "PENDING_INFORMATION").length,
      completed: claims.filter((c) => c.claim_status === "COMPLETED" || c.claim_status === "CLOSED").length,
      flaggedSession: countRecommendations("FLAG_FOR_REVIEW", session),
      requestEvidenceSession: countRecommendations("REQUEST_MORE_EVIDENCE", session),
    };
  }, [data]);

  if (isLoading) return <LoadingState label="Loading dashboard…" />;
  if (error) return <ErrorState message={(error as Error).message} />;

  const recent = (data ?? []).slice(0, 5);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[22px] font-semibold tracking-tight text-text">Overview</h1>
        <p className="text-[13px] text-text-muted">Warranty claim queue and assessment activity</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <StatCard label="Total claims" value={stats.total} />
        <StatCard label="Awaiting review" value={stats.awaiting} />
        <StatCard label="Pending information" value={stats.pendingInfo} />
        <StatCard label="Completed / closed" value={stats.completed} />
        <StatCard label="Flagged (session assessments)" value={stats.flaggedSession} />
        <StatCard label="Request evidence (session)" value={stats.requestEvidenceSession} />
      </div>
      <p className="text-[11px] text-text-faint">
        Recommendation KPIs reflect assessments run in this browser session only.
      </p>
      <Card title="Recent claims">
        <ClaimsTable claims={recent} />
      </Card>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <p className="ui-label">{label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-tight text-text">{value}</p>
    </div>
  );
}

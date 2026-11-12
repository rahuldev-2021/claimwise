import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import { getClaim, getLatestAssessment, runAssessment } from "../api/services";
import { EvidenceSection } from "../features/assessment/EvidenceSection";
import { AiAnalysisWorkspace } from "../features/claims/AiAnalysisWorkspace";
import { AssessmentPromptEmpty } from "../features/claims/AssessmentPromptEmpty";
import { ClaimContextPanel } from "../features/claims/ClaimContextPanel";
import { ClaimDetailHeader } from "../features/claims/ClaimDetailHeader";
import { ClaimInvestigationToolbar } from "../features/claims/ClaimInvestigationToolbar";
import { ReviewerFeedbackPanel } from "../features/reviewer-feedback/ReviewerFeedbackPanel";
import { Tabs, type TabItem } from "../components/ui/Tabs";
import { ErrorState, LoadingState } from "../components/ui/StateMessage";
import { cacheAssessmentSummary } from "../lib/assessmentCache";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthProvider";
import { AssessmentTraceModal } from "../features/assessment/trace/AssessmentTraceModal";
import type { ReviewerDecision } from "../api/types/feedback";
import { dealerCopy } from "../lib/dealerCopy";

type ClaimDetailLocationState = { autoAssess?: boolean; assessWarning?: string } | null;

export function ClaimDetailPage() {
  const { claimId = "" } = useParams();
  const location = useLocation();
  const locationState = location.state as ClaimDetailLocationState;
  const qc = useQueryClient();
  const { user, hasPermission } = useAuth();
  const canAssess = hasPermission("claims:assess");
  const canDecide = hasPermission("claims:assess") || hasPermission("claims:review");
  const [tab, setTab] = useState("ai");
  const [llmEnabled, setLlmEnabled] = useState(true);
  const [autoIngest, setAutoIngest] = useState(true);
  const [financialEnabled, setFinancialEnabled] = useState(true);
  const [traceOpen, setTraceOpen] = useState(false);
  const [traceExpanded, setTraceExpanded] = useState(false);
  const [decisionPreset, setDecisionPreset] = useState<ReviewerDecision | null>(null);
  const autoAssessStarted = useRef(false);
  const openTraceOnSuccessRef = useRef(false);

  const openTrace = () => setTraceOpen(true);

  const claimQuery = useQuery({
    queryKey: ["claim", claimId],
    queryFn: () => getClaim(claimId),
    enabled: Boolean(claimId),
  });

  const latestAssessmentQuery = useQuery({
    queryKey: ["assessment", claimId],
    queryFn: async () => {
      try {
        return await getLatestAssessment(claimId);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          return null;
        }
        throw err;
      }
    },
    enabled: Boolean(claimId),
    staleTime: 60_000,
  });

  const assessMutation = useMutation({
    mutationFn: (opts: { forceRefresh: boolean }) =>
      runAssessment({
        claim_id: claimId,
        top_k: 5,
        auto_ingest: autoIngest,
        llm_enabled: llmEnabled,
        financial_enabled: financialEnabled,
        force_refresh: opts.forceRefresh,
      }),
    onSuccess: (data) => {
      cacheAssessmentSummary(data);
      qc.setQueryData(["assessment", claimId], data);
      setTab("ai");
      if (openTraceOnSuccessRef.current) {
        setTraceOpen(true);
      }
      openTraceOnSuccessRef.current = false;
    },
    onError: () => {
      openTraceOnSuccessRef.current = false;
    },
  });

  const assessment = assessMutation.data ?? latestAssessmentQuery.data ?? null;

  const triggerAssessment = (opts?: { openTrace?: boolean; forceRefresh?: boolean }) => {
    if (!canAssess || assessMutation.isPending) return;
    openTraceOnSuccessRef.current = Boolean(opts?.openTrace);
    const forceRefresh = opts?.forceRefresh ?? Boolean(assessment);
    assessMutation.mutate({ forceRefresh });
  };

  useEffect(() => {
    if (!locationState?.autoAssess || !canAssess || !claimId) return;
    if (autoAssessStarted.current) return;
    if (latestAssessmentQuery.isLoading) return;
    if (assessment) return;
    autoAssessStarted.current = true;
    window.history.replaceState({}, document.title);
    triggerAssessment({ forceRefresh: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- run once after snapshot load
  }, [
    locationState?.autoAssess,
    canAssess,
    claimId,
    assessment,
    latestAssessmentQuery.isLoading,
  ]);

  const assessing = assessMutation.isPending;
  const loadingAssessment =
    latestAssessmentQuery.isLoading && !assessment && !assessing;

  if (claimQuery.isLoading) return <LoadingState label={dealerCopy.loading.claim} />;
  if (claimQuery.error) return <ErrorState message={(claimQuery.error as Error).message} />;
  if (!claimQuery.data) return <ErrorState message="Claim not found" />;

  const claim = claimQuery.data;
  const docCount = claim.supporting_document_ids.length;

  const aiPanel = loadingAssessment ? (
    <LoadingState label={dealerCopy.loading.assessment} />
  ) : assessment ? (
    <AiAnalysisWorkspace claim={claim} assessment={assessment} onShowDetails={openTrace} />
  ) : assessing ? (
    <LoadingState label={dealerCopy.loading.running} />
  ) : (
    <AssessmentPromptEmpty
      canRun={canAssess}
      assessing={assessing}
      onRun={() => triggerAssessment({ openTrace: true, forceRefresh: true })}
    />
  );

  const tabs: TabItem[] = [
    {
      id: "ai",
      label: dealerCopy.tabs.summary,
      panel: aiPanel,
    },
    {
      id: "documents",
      label: docCount > 0 ? `Documents (${docCount})` : "Documents",
      panel: assessment ? (
        <EvidenceSection assessment={assessment} audience="dealer" />
      ) : assessing || loadingAssessment ? (
        <LoadingState label={dealerCopy.loading.evidence} />
      ) : (
        <p className="text-[13px] text-text-muted">
          {docCount === 0 ? dealerCopy.documents.emptyNoDocs : dealerCopy.documents.emptyWithDocs}
        </p>
      ),
    },
    {
      id: "history",
      label: dealerCopy.tabs.history,
      panel: (
        <p className="text-[13px] text-text-muted">
          Status history and audit trail will appear here when claim workflow APIs are connected.
        </p>
      ),
    },
    {
      id: "decision",
      label: dealerCopy.tabs.decision,
      panel: (
        <ReviewerFeedbackPanel
          claimId={claim.claim_id}
          claimStatus={claim.claim_status}
          initialDecision={decisionPreset}
          systemRecommendation={assessment?.recommendation.overall_recommendation ?? "FLAG_FOR_REVIEW"}
        />
      ),
    },
  ];

  return (
    <div className="space-y-2 pb-2">
      <div className="rounded-lg border border-border bg-surface shadow-composer">
        <div className="px-3 py-2">
          <ClaimDetailHeader claim={claim} assessment={assessment} orgName={user?.org_name} compact />
        </div>
        <div className="border-t border-border bg-surface-raised/20 px-3 py-1.5">
          <ClaimInvestigationToolbar
            claim={claim}
            assessment={assessment}
            canAssess={canAssess}
            canDecide={canDecide}
            onRunAssessment={() => triggerAssessment({ openTrace: true, forceRefresh: true })}
            assessing={assessing}
            onOpenDecision={(preset) => {
              if (preset) setDecisionPreset(preset);
              setTab("decision");
            }}
            onOpenFullAssessment={openTrace}
            autoIngest={autoIngest}
            llmEnabled={llmEnabled}
            financialEnabled={financialEnabled}
            onAutoIngest={setAutoIngest}
            onLlmEnabled={setLlmEnabled}
            onFinancialEnabled={setFinancialEnabled}
          />
        </div>
      </div>

      {latestAssessmentQuery.isError ? (
        <ErrorState message={(latestAssessmentQuery.error as Error).message} />
      ) : null}

      {assessMutation.isError ? (
        <ErrorState
          message={
            assessMutation.error instanceof ApiError && assessMutation.error.status === 503
              ? `${assessMutation.error.message} Enable auto-ingest in assessment options or contact an administrator.`
              : (assessMutation.error as Error).message
          }
        />
      ) : null}

      <div
        className={
          docCount > 0
            ? "grid gap-3 xl:grid-cols-[minmax(0,1fr)_220px]"
            : "grid gap-3"
        }
      >
        <div className="min-w-0 rounded-xl border border-border bg-surface px-3 pb-3 pt-0.5 shadow-composer">
          <Tabs items={tabs} active={tab} onChange={setTab} />
        </div>
        {docCount > 0 ? <ClaimContextPanel claim={claim} assessment={assessment} /> : null}
      </div>

      <AssessmentTraceModal
        open={traceOpen}
        expanded={traceExpanded}
        onExpandedChange={setTraceExpanded}
        onClose={() => setTraceOpen(false)}
        claim={claim}
        assessment={assessment}
        loading={assessing}
      />
    </div>
  );
}

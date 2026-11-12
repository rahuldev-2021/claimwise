import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import type { OverallRecommendation } from "../../api/types/assessment";
import type { ClaimStatus } from "../../api/types/claim";
import type { ReviewerDecision, ReviewerFeedbackCreateRequest } from "../../api/types/feedback";
import { listReviewerFeedback, submitReviewerFeedback } from "../../api/services";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { ErrorState } from "../../components/ui/StateMessage";
import { formatDate } from "../../lib/format";
import { dealerClaimStatusLabel, dealerRecommendationLabel } from "../../lib/dealerLabels";

const DECISIONS: ReviewerDecision[] = [
  "APPROVED",
  "REJECTED",
  "REQUESTED_INFO",
  "ESCALATED",
];

const DECISION_LABELS: Record<ReviewerDecision, string> = {
  PENDING: "Pending",
  APPROVED: "Approve claim",
  REJECTED: "Reject claim",
  REQUESTED_INFO: "Request more information",
  ESCALATED: "Escalate for review",
};

export function ReviewerFeedbackPanel({
  claimId,
  systemRecommendation,
  claimStatus,
  initialDecision,
}: {
  claimId: string;
  systemRecommendation: OverallRecommendation;
  claimStatus: ClaimStatus;
  initialDecision?: ReviewerDecision | null;
}) {
  const qc = useQueryClient();
  const historyQuery = useQuery({
    queryKey: ["reviewer-feedback", claimId],
    queryFn: () => listReviewerFeedback(claimId),
  });

  const [decision, setDecision] = useState<ReviewerDecision>(initialDecision ?? "APPROVED");
  const [savedStatus, setSavedStatus] = useState<ClaimStatus | null>(null);

  useEffect(() => {
    if (initialDecision) setDecision(initialDecision);
  }, [initialDecision]);
  const [comments, setComments] = useState("");
  const [overrideRec, setOverrideRec] = useState<OverallRecommendation | "">("");
  const [overrideReason, setOverrideReason] = useState("");
  const [infoItems, setInfoItems] = useState("");

  const submitMutation = useMutation({
    mutationFn: (body: ReviewerFeedbackCreateRequest) => submitReviewerFeedback(body),
    onSuccess: (result) => {
      qc.invalidateQueries({ queryKey: ["reviewer-feedback", claimId] });
      qc.invalidateQueries({ queryKey: ["claim", claimId] });
      qc.invalidateQueries({ queryKey: ["claims"] });
      if (result.updated_claim_status) {
        setSavedStatus(result.updated_claim_status);
      }
      setComments("");
      setOverrideRec("");
      setOverrideReason("");
      setInfoItems("");
    },
  });

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const body: ReviewerFeedbackCreateRequest = {
      claim_id: claimId,
      system_recommendation: systemRecommendation,
      reviewer_decision: decision,
      reviewer_comments: comments,
    };
    if (overrideRec) {
      body.overridden_recommendation = overrideRec;
      body.override_reason = overrideReason;
    }
    if (decision === "REQUESTED_INFO") {
      body.additional_information_requested = infoItems
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean);
    }
    submitMutation.mutate(body);
  };

  return (
    <div className="space-y-4">
      {(claimStatus === "COMPLETED" || claimStatus === "CLOSED") && !savedStatus ? (
        <p className="rounded-lg border border-border bg-surface-raised px-3 py-2 text-[13px] text-text">
          This claim is already <strong>{dealerClaimStatusLabel(claimStatus)}</strong>. Decisions are locked unless
          the claim is reopened in the workflow.
        </p>
      ) : null}
      {savedStatus ? (
        <p className="rounded-lg border border-green-500/30 bg-green-500/10 px-3 py-2 text-[13px] text-text">
          Saved. Claim status is now <strong>{dealerClaimStatusLabel(savedStatus)}</strong> (visible in the header and
          claim list).
        </p>
      ) : null}

      <Card title="Record your decision">
        <form onSubmit={onSubmit} className="space-y-3 text-[13px]">
          <label className="block">
            <span className="text-text-muted">Suggested next step from claim check</span>
            <input
              className="ui-input mt-1 w-full bg-base-deep"
              readOnly
              value={dealerRecommendationLabel(systemRecommendation)}
            />
          </label>
          <label className="block">
            <span className="text-text-muted">Reviewer decision</span>
            <select
              className="ui-input mt-1 w-full"
              value={decision}
              onChange={(e) => setDecision(e.target.value as ReviewerDecision)}
            >
              {DECISIONS.map((d) => (
                <option key={d} value={d}>
                  {DECISION_LABELS[d]}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-text-muted">Comments</span>
            <textarea
              className="ui-input mt-1 w-full"
              rows={3}
              value={comments}
              onChange={(e) => setComments(e.target.value)}
            />
          </label>
          <label className="block">
            <span className="text-text-muted">Override recommendation (optional)</span>
            <select
              className="ui-input mt-1 w-full"
              value={overrideRec}
              onChange={(e) => setOverrideRec(e.target.value as OverallRecommendation | "")}
            >
              <option value="">No override</option>
              <option value="REQUEST_MORE_EVIDENCE">REQUEST_MORE_EVIDENCE</option>
              <option value="FLAG_FOR_REVIEW">FLAG_FOR_REVIEW</option>
              <option value="PROCEED_TO_HUMAN_REVIEW">PROCEED_TO_HUMAN_REVIEW</option>
              <option value="INSUFFICIENT_INFORMATION">INSUFFICIENT_INFORMATION</option>
            </select>
          </label>
          {overrideRec ? (
            <label className="block">
              <span className="text-text-muted">Override reason (required)</span>
              <textarea
                className="ui-input mt-1 w-full"
                rows={2}
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
              />
            </label>
          ) : null}
          {decision === "REQUESTED_INFO" ? (
            <label className="block">
              <span className="text-text-muted">Additional information requested (one per line)</span>
              <textarea
                className="ui-input mt-1 w-full"
                rows={3}
                value={infoItems}
                onChange={(e) => setInfoItems(e.target.value)}
              />
            </label>
          ) : null}
          {submitMutation.isError ? (
            <ErrorState message={(submitMutation.error as Error).message} />
          ) : null}
          <Button
            type="submit"
            disabled={
              submitMutation.isPending || claimStatus === "COMPLETED" || claimStatus === "CLOSED"
            }
          >
            {submitMutation.isPending ? "Saving…" : "Save decision"}
          </Button>
        </form>
      </Card>

      <Card title="Feedback history">
        {historyQuery.isLoading ? <p className="text-sm text-text-muted">Loading…</p> : null}
        {historyQuery.data?.length ? (
          <ul className="space-y-3 text-sm">
            {historyQuery.data.map((f, idx) => (
              <li key={`${f.created_at}-${idx}`} className="rounded border border-border p-3">
                <p className="font-medium">
                  {f.reviewer_decision} · {f.reviewed_at ? formatDate(f.reviewed_at) : ""}
                </p>
                <p className="text-text-muted">{f.reviewer_comments}</p>
                {f.overridden_recommendation ? (
                  <p className="mt-1 text-[11px] text-amber-800">
                    Override: {f.overridden_recommendation} — {f.override_reason}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-text-faint">No reviewer feedback recorded yet.</p>
        )}
      </Card>
    </div>
  );
}

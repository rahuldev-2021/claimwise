import type { OverallRecommendation } from "./assessment";
import type { ClaimStatus } from "./claim";

export type ReviewerDecision =
  | "PENDING"
  | "APPROVED"
  | "REJECTED"
  | "REQUESTED_INFO"
  | "ESCALATED";

export interface ReviewerFeedback {
  claim_id: string;
  system_recommendation: OverallRecommendation;
  reviewer_decision: ReviewerDecision;
  reviewer_comments: string;
  overridden_recommendation?: OverallRecommendation | null;
  override_reason?: string | null;
  additional_information_requested: string[];
  reviewed_at?: string | null;
  created_at: string;
  updated_claim_status?: ClaimStatus | null;
}

export interface ReviewerFeedbackCreateRequest {
  claim_id: string;
  system_recommendation: OverallRecommendation;
  reviewer_decision: ReviewerDecision;
  reviewer_comments?: string;
  overridden_recommendation?: OverallRecommendation | null;
  override_reason?: string | null;
  additional_information_requested?: string[];
}

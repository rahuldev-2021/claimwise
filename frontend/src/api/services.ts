import { getAccessToken } from "../auth/authStore";
import { apiCredentialsDefault, getApiBaseUrl } from "../lib/apiConfig";
import { apiFetch, ApiError } from "./client";
import { endpoints } from "./endpoints";
import type {
  AssessmentAnalyzeRequest,
  ClaimAssessmentResponse,
} from "./types/assessment";
import type { ClaimInput, ClaimStatus } from "./types/claim";
import type { ProcessingStatus } from "./types/processingStatus";
import type {
  ReviewerFeedback,
  ReviewerFeedbackCreateRequest,
} from "./types/feedback";

export interface ListClaimsParams {
  q?: string;
  status?: ClaimStatus;
  repair_category?: string;
  sort?: "submission_date_desc" | "submission_date_asc";
}

export function listClaims(params: ListClaimsParams = {}): Promise<ClaimInput[]> {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  if (params.status) search.set("status", params.status);
  if (params.repair_category) search.set("repair_category", params.repair_category);
  if (params.sort) search.set("sort", params.sort);
  const qs = search.toString();
  return apiFetch<ClaimInput[]>(`${endpoints.claims}${qs ? `?${qs}` : ""}`);
}

export function getClaim(claimId: string): Promise<ClaimInput> {
  return apiFetch<ClaimInput>(endpoints.claim(claimId));
}

export function getClaimProcessingStatus(claimId: string): Promise<ProcessingStatus> {
  return apiFetch<ProcessingStatus>(endpoints.claimProcessingStatus(claimId));
}

export type CreateClaimPayload = {
  repair_order: string;
  vin: string | null;
  year: string;
  make: string;
  model: string;
  category: string;
  customer_complaint: string;
  technician_diagnosis: string;
  recommended_repair: string;
  parts_cost: string;
  labour_hours: string;
  currency?: string;
  mileage?: string;
  engine_type?: string;
};

export async function createClaim(
  payload: CreateClaimPayload,
  files: File[] = [],
): Promise<ClaimInput> {
  const form = new FormData();
  form.append("payload", JSON.stringify(payload));
  for (const file of files) {
    form.append("files", file);
  }
  const token = getAccessToken();
  const response = await fetch(`${getApiBaseUrl()}${endpoints.claims}`, {
    method: "POST",
    body: form,
    credentials: apiCredentialsDefault(),
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  const text = await response.text();
  const data = text ? (JSON.parse(text) as unknown) : undefined;
  if (!response.ok) {
    const detail =
      typeof data === "object" && data !== null && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : response.statusText;
    throw new ApiError(detail, response.status, data);
  }
  return data as ClaimInput;
}

export function runAssessment(
  body: AssessmentAnalyzeRequest,
): Promise<ClaimAssessmentResponse> {
  return apiFetch<ClaimAssessmentResponse>(endpoints.assessmentAnalyze, {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs: 300_000,
  });
}

export function getLatestAssessment(claimId: string): Promise<ClaimAssessmentResponse> {
  return apiFetch<ClaimAssessmentResponse>(endpoints.assessmentLatest(claimId));
}

export function listReviewerFeedback(claimId: string): Promise<ReviewerFeedback[]> {
  return apiFetch<ReviewerFeedback[]>(endpoints.reviewerFeedbackForClaim(claimId));
}

export function submitReviewerFeedback(
  body: ReviewerFeedbackCreateRequest,
): Promise<ReviewerFeedback> {
  return apiFetch<ReviewerFeedback>(endpoints.reviewerFeedback, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function fetchHealth(): Promise<{ status: string }> {
  return apiFetch(endpoints.health);
}

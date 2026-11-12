const API_PREFIX = "/api/v1";

export const endpoints = {
  health: "/health",
  claims: `${API_PREFIX}/claims`,
  claim: (id: string) => `${API_PREFIX}/claims/${encodeURIComponent(id)}`,
  claimProcessingStatus: (id: string) =>
    `${API_PREFIX}/claims/${encodeURIComponent(id)}/processing-status`,
  assessmentAnalyze: `${API_PREFIX}/assessment/analyze`,
  assessmentLatest: (claimId: string) =>
    `${API_PREFIX}/claims/${encodeURIComponent(claimId)}/assessment/latest`,
  reviewerFeedback: `${API_PREFIX}/reviewer-feedback`,
  reviewerFeedbackForClaim: (id: string) =>
    `${API_PREFIX}/reviewer-feedback/${encodeURIComponent(id)}`,
  ragHealth: `${API_PREFIX}/rag/health`,
  llmHealth: `${API_PREFIX}/llm/health`,
} as const;

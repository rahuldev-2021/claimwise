import type { ClaimAssessmentResponse, OverallRecommendation } from "../api/types/assessment";

const SESSION_KEY = "claimwise:assessment-summaries";

export interface AssessmentSummaryCache {
  claim_id: string;
  overall_recommendation: OverallRecommendation;
  technical_status: string;
  assessed_at: string;
}

function readAll(): AssessmentSummaryCache[] {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as AssessmentSummaryCache[];
  } catch {
    return [];
  }
}

function writeAll(items: AssessmentSummaryCache[]): void {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(items));
}

export function cacheAssessmentSummary(result: ClaimAssessmentResponse): void {
  const items = readAll().filter((x) => x.claim_id !== result.claim_id);
  items.push({
    claim_id: result.claim_id,
    overall_recommendation: result.recommendation.overall_recommendation,
    technical_status: result.technical_validation.technical_status,
    assessed_at: new Date().toISOString(),
  });
  writeAll(items);
}

export function getCachedAssessmentSummaries(): AssessmentSummaryCache[] {
  return readAll();
}

export function countRecommendations(
  rec: OverallRecommendation,
  items = readAll(),
): number {
  return items.filter((x) => x.overall_recommendation === rec).length;
}

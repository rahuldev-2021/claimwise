export type FinancialStatus =
  | "WITHIN_EXPECTED_RANGE"
  | "OUTSIDE_EXPECTED_RANGE"
  | "INSUFFICIENT_DATA"
  | "NEEDS_REVIEW";

export type FinancialAssessmentStatus = "PENDING" | "AVAILABLE" | "UNAVAILABLE";

export interface PredictionInterval {
  low: string;
  typical: string;
  high: string;
}

export interface FinancialValidationResult {
  claim_id: string;
  submitted_parts_cost: string;
  predicted_parts_cost?: string | null;
  submitted_labour_hours: string;
  predicted_labour_hours?: string | null;
  parts_discrepancy_pct?: string | null;
  labour_discrepancy_pct?: string | null;
  parts_prediction_interval?: PredictionInterval | null;
  labour_prediction_interval?: PredictionInterval | null;
  financial_status: FinancialStatus;
  explanation: string;
  triggered_financial_rules: string[];
  parts_model_version?: string | null;
  labour_model_version?: string | null;
  parts_model_algorithm?: string | null;
  labour_model_algorithm?: string | null;
  model_lifecycle?: string | null;
  experimental_prediction?: boolean;
  synthetic_data_prediction?: boolean;
  human_review_required: boolean;
  limitations: string;
}

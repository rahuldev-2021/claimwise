export type StageStatus =
  | "PENDING"
  | "QUEUED"
  | "PROCESSING"
  | "COMPLETED"
  | "FAILED"
  | "SKIPPED";

export type OverallStatus = "PROCESSING" | "READY" | "FAILED";

export interface DocumentStageStatus {
  status: StageStatus;
  total: number;
  processed: number;
  failed: number;
}

export interface SimpleStageStatus {
  status: StageStatus;
  error?: string | null;
}

export interface ProcessingStatus {
  overall: OverallStatus;
  documents: DocumentStageStatus;
  nlp: SimpleStageStatus;
  rag: SimpleStageStatus;
  technical_validation: SimpleStageStatus;
  financial_validation: SimpleStageStatus;
  recommendation: SimpleStageStatus;
  last_updated_at: string;
}

import type { ProcessingStatus, SimpleStageStatus, StageStatus } from "../api/types/processingStatus";

const STAGE_LABEL: Record<string, string> = {
  PENDING: "Pending",
  QUEUED: "Queued",
  PROCESSING: "Running",
  COMPLETED: "Done",
  FAILED: "Failed",
  SKIPPED: "Skipped",
};

export function formatStageStatus(stage: SimpleStageStatus): string {
  const base = STAGE_LABEL[stage.status] ?? stage.status;
  if (stage.status === "SKIPPED") return "Skipped (not run)";
  if (stage.status === "FAILED" && stage.error) {
    return `Failed — ${stage.error}`;
  }
  return base;
}

/** Short label for status column (enterprise table). */
export function stageStatusShort(status: StageStatus): string {
  return STAGE_LABEL[status] ?? status;
}

export function stageDetail(stage: SimpleStageStatus, fallback = "—"): string {
  if (stage.status === "FAILED" && stage.error) return stage.error;
  if (stage.status === "SKIPPED") return "Not run for this claim";
  if (stage.status === "PENDING") return "Waiting";
  if (stage.status === "QUEUED") return "Queued";
  if (stage.status === "PROCESSING") return "In progress";
  return fallback;
}

export function stageTone(status: StageStatus): "ok" | "warn" | "err" | "mute" {
  switch (status) {
    case "COMPLETED":
      return "ok";
    case "FAILED":
      return "err";
    case "PROCESSING":
    case "QUEUED":
      return "warn";
    case "SKIPPED":
      return "mute";
    default:
      return "mute";
  }
}

export type OverallDisplay = {
  label: string;
  detail?: string;
  tone: "ok" | "warn" | "err" | "mute";
};

/** UI summary that reflects stage failures, not only `overall` from the API. */
export function deriveProcessingOverall(status: ProcessingStatus): OverallDisplay {
  const failed: string[] = [];
  const check = (name: string, stage: SimpleStageStatus) => {
    if (stage.status === "FAILED") {
      failed.push(stage.error ? `${name}: ${stage.error}` : `${name} failed`);
    }
  };
  check("RAG", status.rag);
  check("NLP", status.nlp);
  check("Documents", { status: status.documents.status, error: null });
  if (status.documents.failed > 0) {
    failed.push(`Documents: ${status.documents.failed} failed to process`);
  }
  check("Technical validation", status.technical_validation);
  check("Financial validation", status.financial_validation);
  check("Recommendation", status.recommendation);

  if (failed.length > 0) {
    return {
      label: "Issues detected",
      detail: failed[0],
      tone: "err",
    };
  }
  if (status.overall === "PROCESSING") {
    return { label: "Processing", tone: "warn" };
  }
  if (status.overall === "FAILED") {
    return { label: "Failed", tone: "err" };
  }
  const skipped = [
    status.financial_validation.status === "SKIPPED" ? "Financial validation skipped" : null,
    status.recommendation.status === "SKIPPED" ? "Recommendation skipped" : null,
  ].filter(Boolean);
  if (skipped.length > 0) {
    return { label: "Ready with skipped stages", detail: skipped.join("; "), tone: "warn" };
  }
  return { label: "Ready", tone: "ok" };
}

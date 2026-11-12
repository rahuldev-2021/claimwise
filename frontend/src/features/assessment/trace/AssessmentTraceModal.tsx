import { Maximize2, Minimize2, X } from "lucide-react";
import { useEffect } from "react";
import { createPortal } from "react-dom";
import type { ClaimAssessmentResponse } from "../../../api/types/assessment";
import type { ClaimInput } from "../../../api/types/claim";
import { AssessmentReportDownload } from "../AssessmentReportDownload";
import { traceSubtitle } from "./assessmentTraceModel";
import { AssessmentTraceTimeline } from "./AssessmentTraceTimeline";

export function AssessmentTraceModal({
  open,
  expanded,
  onExpandedChange,
  onClose,
  claim,
  assessment,
  loading = false,
}: {
  open: boolean;
  expanded: boolean;
  onExpandedChange: (expanded: boolean) => void;
  onClose: () => void;
  claim: ClaimInput;
  assessment: ClaimAssessmentResponse | null;
  loading?: boolean;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.document.addEventListener("keydown", onKey);
    const prev = window.document.body.style.overflow;
    window.document.body.style.overflow = "hidden";
    return () => {
      window.document.removeEventListener("keydown", onKey);
      window.document.body.style.overflow = prev;
    };
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div
      className={
        expanded
          ? "fixed inset-0 z-[80] flex flex-col bg-base"
          : "fixed inset-0 z-[80] flex items-center justify-center p-3 sm:p-6"
      }
    >
      {!expanded ? (
        <button type="button" className="absolute inset-0 bg-black/65" aria-label="Close assessment trace" onClick={onClose} />
      ) : null}

      <div
        className={
          expanded
            ? "flex min-h-0 flex-1 flex-col"
            : "relative flex h-[min(92vh,900px)] w-full max-w-5xl flex-col overflow-hidden rounded-xl border border-border bg-surface shadow-2xl"
        }
        role="dialog"
        aria-modal="true"
        aria-label="Full assessment trace"
      >
        <header className="flex shrink-0 items-center gap-3 border-b border-border px-4 py-3 sm:px-5">
          <div className="min-w-0 flex-1">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-accent">Assessment trace</p>
            <h2 className="truncate text-[15px] font-semibold text-text">NLP → RAG → technical → financial → recommendation</h2>
            <p className="mt-0.5 truncate text-[12px] text-text-muted">{traceSubtitle(claim)}</p>
          </div>
          <div className="flex shrink-0 items-center gap-1">
            <AssessmentReportDownload claim={claim} assessment={assessment} compact />
            <button
              type="button"
              onClick={() => onExpandedChange(!expanded)}
              className="rounded-md p-2 text-text-muted hover:bg-surface-hover hover:text-text"
              aria-label={expanded ? "Exit full screen" : "Expand full screen"}
              title={expanded ? "Exit full screen" : "Expand full screen"}
            >
              {expanded ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="rounded-md p-2 text-text-muted hover:bg-surface-hover hover:text-text"
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto scrollbar-thin">
          <AssessmentTraceTimeline claim={claim} assessment={assessment} loading={loading} expanded={expanded} />
        </div>
      </div>
    </div>,
    window.document.body,
  );
}

import { ChevronDown, Download } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ClaimAssessmentResponse } from "../../api/types/assessment";
import type { ClaimInput } from "../../api/types/claim";
import { AnchoredDropdown, isAnchoredDropdownTarget } from "../../components/ui/AnchoredDropdown";
import { Button } from "../../components/ui/Button";
import {
  downloadAssessmentReportDoc,
  printAssessmentReportPdf,
} from "../../lib/assessmentReportExport";

export function AssessmentReportDownload({
  claim,
  assessment,
  compact = false,
  busy = false,
}: {
  claim: ClaimInput;
  assessment: ClaimAssessmentResponse | null;
  compact?: boolean;
  busy?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const anchorRef = useRef<HTMLDivElement>(null);
  const disabled = !assessment || busy;

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      const target = e.target as Node;
      if (anchorRef.current?.contains(target)) return;
      if (isAnchoredDropdownTarget(e.target)) return;
      setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  const onDoc = () => {
    if (!assessment) return;
    downloadAssessmentReportDoc(claim, assessment);
    setOpen(false);
  };

  const onPdf = () => {
    if (!assessment) return;
    printAssessmentReportPdf(claim, assessment);
    setOpen(false);
  };

  const menu = (
    <AnchoredDropdown open={open} anchorRef={anchorRef} align="right">
      <button
        type="button"
        className="block w-full px-3 py-2 text-left text-[13px] text-text hover:bg-surface-hover"
        onClick={onDoc}
      >
        Word document (.doc)
      </button>
      <button
        type="button"
        className="block w-full px-3 py-2 text-left text-[13px] text-text hover:bg-surface-hover"
        onClick={onPdf}
      >
        PDF (print / Save as PDF)
      </button>
      <p className="border-t border-border px-3 py-2 text-[10px] leading-snug text-text-faint">
        PDF opens print; choose &quot;Save as PDF&quot; in the dialog. No server upload.
      </p>
    </AnchoredDropdown>
  );

  if (compact) {
    return (
      <div className="relative shrink-0" ref={anchorRef}>
        <Button
          type="button"
          variant="secondary"
          disabled={disabled}
          onClick={() => setOpen((v) => !v)}
          title={disabled ? "Run assessment first" : "Download report (Word or PDF)"}
          aria-label="Download assessment report"
        >
          <Download className="h-4 w-4" />
        </Button>
        {assessment ? menu : null}
      </div>
    );
  }

  return (
    <div className="relative shrink-0" ref={anchorRef}>
      <Button
        type="button"
        variant="secondary"
        className="whitespace-nowrap"
        disabled={disabled}
        title={disabled ? "Run assessment first" : undefined}
        onClick={() => setOpen((v) => !v)}
      >
        <Download className="mr-1.5 h-4 w-4 shrink-0" />
        Export
        <ChevronDown className="ml-1 h-4 w-4 shrink-0" />
      </Button>
      {assessment ? menu : null}
    </div>
  );
}

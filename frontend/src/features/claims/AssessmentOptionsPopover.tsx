import { Settings2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { AnchoredDropdown, isAnchoredDropdownTarget } from "../../components/ui/AnchoredDropdown";
import { Button } from "../../components/ui/Button";
import { dealerCopy } from "../../lib/dealerCopy";

export function AssessmentOptionsPopover({
  autoIngest,
  llmEnabled,
  financialEnabled,
  disabled,
  onAutoIngest,
  onLlmEnabled,
  onFinancialEnabled,
}: {
  autoIngest: boolean;
  llmEnabled: boolean;
  financialEnabled: boolean;
  disabled?: boolean;
  onAutoIngest: (v: boolean) => void;
  onLlmEnabled: (v: boolean) => void;
  onFinancialEnabled: (v: boolean) => void;
}) {
  const [open, setOpen] = useState(false);
  const anchorRef = useRef<HTMLDivElement>(null);

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

  return (
    <div className="relative shrink-0" ref={anchorRef}>
      <Button
        type="button"
        variant="secondary"
        disabled={disabled}
        onClick={() => setOpen((v) => !v)}
        title={dealerCopy.actions.claimCheckOptions}
        aria-expanded={open}
      >
        <Settings2 className="h-4 w-4" />
      </Button>
      <AnchoredDropdown open={open} anchorRef={anchorRef} align="right" widthClass="w-64" className="p-3 text-[12px]">
        <p className="mb-2 font-semibold text-text">{dealerCopy.options.title}</p>
        <div className="space-y-2 text-text-muted">
          <label className="flex cursor-pointer items-center gap-2">
            <input
              type="checkbox"
              className="rounded border-border"
              checked={autoIngest}
              onChange={(e) => onAutoIngest(e.target.checked)}
            />
            {dealerCopy.options.autoIngest}
          </label>
          <label className="flex cursor-pointer items-center gap-2">
            <input
              type="checkbox"
              className="rounded border-border"
              checked={llmEnabled}
              onChange={(e) => onLlmEnabled(e.target.checked)}
            />
            {dealerCopy.options.llmSummary}
          </label>
          <label className="flex cursor-pointer items-center gap-2">
            <input
              type="checkbox"
              className="rounded border-border"
              checked={financialEnabled}
              onChange={(e) => onFinancialEnabled(e.target.checked)}
            />
            {dealerCopy.options.financial}
          </label>
        </div>
      </AnchoredDropdown>
    </div>
  );
}

import { Sparkles } from "lucide-react";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { dealerCopy } from "../../lib/dealerCopy";

export function AssessmentPromptEmpty({
  canRun,
  assessing,
  onRun,
  processingNote,
}: {
  canRun: boolean;
  assessing: boolean;
  onRun: () => void;
  processingNote?: string | null;
}) {
  return (
    <Card className="border-dashed border-border-strong bg-surface-raised/40 p-6">
      <div className="mx-auto flex max-w-lg flex-col items-center text-center">
        <div className="mb-3 rounded-full bg-primary/10 p-2.5 text-primary">
          <Sparkles className="h-5 w-5" aria-hidden />
        </div>
        <h2 className="text-[15px] font-semibold text-text">{dealerCopy.assessmentEmpty.title}</h2>
        <p className="mt-2 text-[13px] leading-relaxed text-text-muted">{dealerCopy.assessmentEmpty.body}</p>
        {processingNote ? (
          <p className="mt-2 text-[12px] text-text-muted">{processingNote}</p>
        ) : null}
        <Button
          type="button"
          variant="primary"
          className="mt-4"
          disabled={!canRun || assessing}
          onClick={onRun}
          title={!canRun ? "Requires claims:assess" : undefined}
        >
          {assessing ? dealerCopy.actions.runningClaimCheck : dealerCopy.actions.runClaimCheck}
        </Button>
        {!canRun ? (
          <p className="mt-2 text-[11px] text-text-faint">{dealerCopy.assessmentEmpty.noPermission}</p>
        ) : null}
      </div>
    </Card>
  );
}

import { Plus, Send } from "lucide-react";

export function ClaimInvestigationComposer({ claimId }: { claimId: string }) {
  return (
    <div className="sticky bottom-0 border-t border-border bg-base/95 pb-1 pt-3 backdrop-blur-sm">
      <div className="rounded-[28px] border border-border bg-surface px-3 py-2 shadow-composer">
        <div className="flex items-end gap-2">
          <button
            type="button"
            className="rounded-full p-2 text-text-faint hover:bg-surface-hover"
            aria-label="Add attachment"
            title="Attachments (coming soon)"
          >
            <Plus className="h-4 w-4" />
          </button>
          <textarea
            readOnly
            rows={1}
            placeholder={`Ask about claim ${claimId}—grounded chat (Phase 7B)`}
            className="max-h-32 min-h-[40px] flex-1 resize-none bg-transparent px-1 py-2 text-[14px] text-text placeholder:text-text-faint focus:outline-none"
          />
          <button
            type="button"
            disabled
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent text-accent-fg opacity-50"
            aria-label="Send"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

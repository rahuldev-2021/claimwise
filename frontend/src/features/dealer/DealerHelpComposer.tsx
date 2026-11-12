import { Info, Send } from "lucide-react";

export function DealerHelpComposer() {
  return (
    <div className="mt-auto border-t border-border bg-base px-4 pb-5 pt-4">
      <div className="mx-auto max-w-[1120px]">
        <div className="flex items-center gap-2 rounded-2xl border border-border bg-surface px-3 py-2 shadow-composer">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
            <Info className="h-4 w-4" strokeWidth={1.75} />
          </span>
          <input
            readOnly
            type="text"
            placeholder="Need help? Ask CLAIMWISE anything about your claim…"
            className="min-w-0 flex-1 bg-transparent text-[14px] text-text placeholder:text-text-faint focus:outline-none"
          />
          <button
            type="button"
            disabled
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary text-primary-fg transition hover:bg-primary-hover disabled:opacity-50"
            aria-label="Send"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

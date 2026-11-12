import { FileSearch, MessageSquare, Scale, ShieldAlert } from "lucide-react";
import { Link } from "react-router-dom";
const suggestions = [
  {
    title: "Review queue",
    body: "Open claims awaiting warranty agent review and AI assessment.",
    to: "/claims",
    icon: FileSearch,
  },
  {
    title: "Flagged financials",
    body: "Inspect submitted vs predicted parts and labour when models are available.",
    to: "/claims",
    icon: Scale,
  },
  {
    title: "Evidence gaps",
    body: "Check technical validation and missing documentation before deciding.",
    to: "/claims",
    icon: ShieldAlert,
  },
  {
    title: "Ask about a claim",
    body: "Select a claim, then use assessment tabs for grounded review (chat coming soon).",
    to: "/claims",
    icon: MessageSquare,
  },
];

export function ReviewerWorkspacePage() {
  return (
    <div className="flex h-full min-h-[calc(100vh-8rem)] flex-col">
      <div className="flex flex-1 flex-col items-center justify-center px-4 pb-28">
        <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-surface ring-1 ring-border">
          <img src="/favicon.png" alt="" className="h-6 w-6 object-contain" width={24} height={24} />
        </div>
        <h1 className="text-center text-xl font-semibold tracking-tight text-text">
          How can CLAIMWISE help?
        </h1>
        <p className="mt-2 max-w-md text-center text-[13px] text-text-muted">
          Review dealer submissions, AI assessments, and evidence — then record your warranty
          decision. AI never approves or rejects claims automatically.
        </p>

        <div className="mt-8 grid w-full max-w-2xl gap-3 sm:grid-cols-2">
          {suggestions.map(({ title, body, to, icon: Icon }) => (
            <Link
              key={title}
              to={to}
              className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-accent/25 hover:bg-surface-hover"
            >
              <Icon className="mb-2 h-4 w-4 text-text-muted" />
              <p className="text-[13px] font-medium text-text">{title}</p>
              <p className="mt-1 text-[12px] leading-relaxed text-text-faint">{body}</p>
            </Link>
          ))}
        </div>
      </div>

      <div className="sticky bottom-0 mx-auto w-full max-w-3xl px-4 pb-2">
        <div className="rounded-[28px] border border-border bg-surface px-3 py-2 shadow-composer">
          <div className="flex items-end gap-2">
            <textarea
              readOnly
              rows={1}
              placeholder="Ask about the selected claim"
              className="max-h-40 min-h-[40px] flex-1 resize-none bg-transparent px-2 py-2 text-[15px] text-text placeholder:text-text-faint focus:outline-none"
            />
            <button
              type="button"
              disabled
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent text-accent-fg opacity-50"
              aria-label="Send"
            >
              ↑
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

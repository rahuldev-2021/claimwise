import type { DealerClaimResponse } from "../../api/types/assessment";
import { Badge } from "../../components/ui/Badge";
import { dealerCopy } from "../../lib/dealerCopy";
import { dealerClaimResponseVerdictTone } from "../../lib/dealerLabels";

export function ClaimResponseCard({ response }: { response: DealerClaimResponse }) {
  return (
    <section className="rounded-lg border border-border bg-base-deep/40 p-2.5 ring-1 ring-border/80">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">
          {dealerCopy.sections.response}
        </span>
        <Badge tone={dealerClaimResponseVerdictTone(response.verdict)}>{response.verdict_label}</Badge>
      </div>

      <p className="mt-1.5 text-[13px] font-medium leading-snug text-text">{response.summary}</p>

      {response.because.length > 0 ? (
        <ul className="mt-2 flex flex-col gap-1 sm:flex-row sm:flex-wrap sm:gap-1.5">
          {response.because.map((line) => (
            <li
              key={line.slice(0, 48)}
              className="rounded-md border border-border/80 bg-surface px-2 py-1 text-[11px] leading-snug text-text-muted"
            >
              {line}
            </li>
          ))}
        </ul>
      ) : null}

      {response.what_to_say ? (
        <div className="mt-2 border-l-2 border-primary/60 bg-surface/80 py-1.5 pl-2.5 pr-2">
          <p className="text-[9px] font-bold uppercase tracking-wider text-text-muted">
            {dealerCopy.sections.responseSay}
          </p>
          <p className="mt-0.5 text-[12px] leading-relaxed text-text">{response.what_to_say}</p>
        </div>
      ) : null}
    </section>
  );
}

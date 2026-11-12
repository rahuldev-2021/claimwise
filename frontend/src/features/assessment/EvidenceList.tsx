import type { EvidenceItem } from "../../api/types/assessment";
import { Badge } from "../../components/ui/Badge";
import { formatScore } from "../../lib/format";

export function EvidenceList({
  items,
  variant,
}: {
  items: EvidenceItem[];
  variant: "supporting" | "contradictory" | "contextual";
}) {
  if (!items.length) return null;

  const border =
    variant === "contradictory"
      ? "border-status-err/25 bg-status-err/5"
      : variant === "contextual"
        ? "border-border bg-surface-raised"
        : "border-status-ok/20 bg-status-ok/5";

  return (
    <ul className="space-y-2">
      {items.map((e) => (
        <li
          key={`${e.document_id}-${e.chunk_id ?? e.relevant_excerpt.slice(0, 24)}`}
          className={`rounded-lg border px-3 py-2.5 text-[13px] ${border}`}
        >
          <div className="mb-1.5 flex flex-wrap items-center gap-2">
            <span className="font-medium text-text">{e.title ?? e.document_id}</span>
            {e.document_type ? <Badge tone="slate">{e.document_type}</Badge> : null}
            {e.support_class ? <Badge tone="blue">{e.support_class}</Badge> : null}
            {e.verification_status ? (
              <Badge tone={e.verification_status === "VERIFIED" ? "green" : "amber"}>
                {e.verification_status}
              </Badge>
            ) : null}
          </div>
          <p className="leading-relaxed text-text-muted">{e.relevant_excerpt}</p>
          {(e.retrieval_score != null || e.quality_score != null) && (
            <p className="mt-2 text-[11px] text-text-faint">
              Retrieval {formatScore(e.retrieval_score)} · Quality {formatScore(e.quality_score)}
            </p>
          )}
        </li>
      ))}
    </ul>
  );
}

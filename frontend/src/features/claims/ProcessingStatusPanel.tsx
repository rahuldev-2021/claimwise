import { Fragment } from "react";
import type { ProcessingStatus, StageStatus } from "../../api/types/processingStatus";
import { Badge } from "../../components/ui/Badge";
import {
  deriveProcessingOverall,
  stageDetail,
  stageStatusShort,
  stageTone,
} from "../../lib/processingDisplay";

const pillTone: Record<ReturnType<typeof stageTone>, "green" | "amber" | "red" | "slate"> = {
  ok: "green",
  warn: "amber",
  err: "red",
  mute: "slate",
};

function StatusPill({ status }: { status: StageStatus }) {
  return <Badge tone={pillTone[stageTone(status)]}>{stageStatusShort(status)}</Badge>;
}

function PipelineRow({
  stage,
  status,
  detail,
}: {
  stage: string;
  status: StageStatus;
  detail: string;
}) {
  return (
    <tr className="border-t border-border/80">
      <td className="py-2 pr-3 font-medium text-text">{stage}</td>
      <td className="w-28 py-2 pr-3">
        <StatusPill status={status} />
      </td>
      <td className="py-2 text-[12px] leading-snug text-text-muted">{detail}</td>
    </tr>
  );
}

function GroupHeader({ label }: { label: string }) {
  return (
    <tr className="bg-surface-raised/50">
      <td colSpan={3} className="py-1.5 text-[10px] font-semibold uppercase tracking-wider text-text-faint">
        {label}
      </td>
    </tr>
  );
}

type Section = {
  title: string;
  rows: { stage: string; status: StageStatus; detail: string }[];
};

export function ProcessingStatusPanel({ status, embedded }: { status: ProcessingStatus; embedded?: boolean }) {
  const overall = deriveProcessingOverall(status);

  const docStatus = status.documents.status;
  const docDetail =
    status.documents.total === 0
      ? "No supporting documents on claim"
      : `${status.documents.processed} of ${status.documents.total} processed${
          status.documents.failed > 0 ? ` · ${status.documents.failed} failed` : ""
        }`;

  const sections: Section[] = [
    {
      title: "Document intelligence",
      rows: [
        { stage: "Documents", status: docStatus, detail: docDetail },
        { stage: "NLP extraction", status: status.nlp.status, detail: stageDetail(status.nlp) },
        { stage: "RAG retrieval", status: status.rag.status, detail: stageDetail(status.rag) },
      ],
    },
    {
      title: "Assessment",
      rows: [
        {
          stage: "Technical validation",
          status: status.technical_validation.status,
          detail: stageDetail(status.technical_validation),
        },
        {
          stage: "Financial validation",
          status: status.financial_validation.status,
          detail: stageDetail(status.financial_validation),
        },
        {
          stage: "Recommendation",
          status: status.recommendation.status,
          detail: stageDetail(status.recommendation),
        },
      ],
    },
  ];

  const failures = sections.flatMap((s) => s.rows).filter((r) => r.status === "FAILED");

  const overallBadgeTone =
    overall.tone === "ok" ? "green" : overall.tone === "warn" ? "amber" : overall.tone === "err" ? "red" : "slate";

  const shell = embedded ? "" : "rounded-xl border border-border bg-surface shadow-composer";

  return (
    <section className={shell}>
      <div
        className={`flex flex-wrap items-center justify-between gap-2 ${
          embedded ? "pb-2" : "border-b border-border px-4 py-2.5"
        }`}
      >
        <div>
          <h2 className="text-[11px] font-semibold uppercase tracking-wider text-text-faint">Assessment pipeline</h2>
          <p className="mt-0.5 text-[12px] text-text-muted">Ingestion and analysis stages</p>
        </div>
        <Badge tone={overallBadgeTone}>{overall.label}</Badge>
      </div>

      <div className={embedded ? "" : "px-4 py-2"}>
        <table className="w-full text-left text-[13px]">
          <thead>
            <tr className="text-[10px] font-semibold uppercase tracking-wide text-text-faint">
              <th className="pb-1 font-semibold">Stage</th>
              <th className="w-28 pb-1 font-semibold">Status</th>
              <th className="pb-1 font-semibold">Detail</th>
            </tr>
          </thead>
          <tbody>
            {sections.map((section) => (
              <Fragment key={section.title}>
                <GroupHeader label={section.title} />
                {section.rows.map((row) => (
                  <PipelineRow key={row.stage} stage={row.stage} status={row.status} detail={row.detail} />
                ))}
              </Fragment>
            ))}
          </tbody>
        </table>

        {failures.length > 0 ? (
          <div className="mt-3 rounded-lg border border-status-err/25 bg-status-err/5 px-3 py-2">
            <p className="text-[11px] font-semibold text-status-err">Action required</p>
            <ul className="mt-1 space-y-1 text-[12px] text-text-muted">
              {failures.map((f) => (
                <li key={f.stage}>
                  <span className="font-medium text-text">{f.stage}:</span> {f.detail}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </section>
  );
}

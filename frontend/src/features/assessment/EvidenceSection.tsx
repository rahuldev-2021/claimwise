import type { ClaimAssessmentResponse } from "../../api/types/assessment";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/StateMessage";
import { formatScore } from "../../lib/format";
import { dealerCopy } from "../../lib/dealerCopy";

export function EvidenceSection({
  assessment,
  audience = "technical",
}: {
  assessment: ClaimAssessmentResponse;
  audience?: "dealer" | "technical";
}) {
  const passages = assessment.retrieval.passages ?? [];
  const qualityByChunk = new Map(
    assessment.technical_validation.supporting_evidence
      .filter((e) => e.chunk_id)
      .map((e) => [e.chunk_id as string, e.quality_score]),
  );

  const isDealer = audience === "dealer";

  if (!passages.length) {
    return (
      <Card title={isDealer ? dealerCopy.documents.evidenceTitle : "Retrieved evidence"}>
        <EmptyState
          message={
            isDealer
              ? dealerCopy.documents.emptyRetrieval
              : "No passages retrieved. Run assessment with RAG ingest or auto_ingest enabled."
          }
        />
      </Card>
    );
  }

  const onlyHistory = passages.every((p) => p.document_type === "REPAIR_HISTORY");

  return (
    <div className="space-y-4">
      {onlyHistory ? (
        <p
          className={
            isDealer
              ? "rounded-md border border-border bg-surface-raised p-3 text-[13px] text-text-muted"
              : "rounded-md border border-amber-200 bg-amber-50 p-3 text-[13px] text-amber-900"
          }
        >
          {isDealer
            ? dealerCopy.documents.historyNote
            : "Only historical repair records were retrieved. History supports context but is not proof of the current failure."}
        </p>
      ) : null}
      {passages.map((p) => {
        const quality = p.chunk_id ? qualityByChunk.get(p.chunk_id) : undefined;
        return (
          <Card key={p.chunk_id} title={p.title || (isDealer ? "Document excerpt" : p.title)}>
            {isDealer ? (
              <div className="mb-2 flex flex-wrap gap-2 text-xs">
                <Badge tone={p.verification_status === "VERIFIED" ? "green" : "amber"}>
                  {p.verification_status === "VERIFIED"
                    ? dealerCopy.documents.verified
                    : dealerCopy.documents.unverified}
                </Badge>
              </div>
            ) : (
              <div className="mb-2 flex flex-wrap gap-2 text-xs">
                <Badge tone="slate">{p.document_id}</Badge>
                <Badge tone="blue">{p.document_type}</Badge>
                <Badge tone={p.verification_status === "VERIFIED" ? "green" : "amber"}>
                  {p.verification_status}
                </Badge>
                {p.evidence_scope ? <Badge tone="slate">{p.evidence_scope}</Badge> : null}
                {p.evidence_source_type ? <Badge tone="slate">{p.evidence_source_type}</Badge> : null}
              </div>
            )}
            <p className="mb-3 whitespace-pre-wrap text-[13px] text-text">{p.text}</p>
            {isDealer ? null : (
              <>
                <dl className="grid gap-2 text-[11px] text-text-muted sm:grid-cols-3">
                  <div>
                    <dt>Retrieval score</dt>
                    <dd className="font-medium text-text">{formatScore(p.score)}</dd>
                  </div>
                  <div>
                    <dt>Evidence quality score</dt>
                    <dd className="font-medium text-text">{formatScore(quality)}</dd>
                  </div>
                  <div>
                    <dt>Rank</dt>
                    <dd>{p.rank}</dd>
                  </div>
                </dl>
                <p className="mt-2 text-[11px] text-text-faint">
                  High retrieval similarity does not prove the repair is technically justified.
                </p>
              </>
            )}
          </Card>
        );
      })}
    </div>
  );
}

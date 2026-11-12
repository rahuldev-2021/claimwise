import { FileText } from "lucide-react";
import type { ClaimInput } from "../../api/types/claim";

export function ClaimAttachmentsList({ claim }: { claim: ClaimInput }) {
  const ids = claim.supporting_document_ids;

  return (
    <div>
      <p className="ui-label mb-2">Documents ({ids.length})</p>
      {ids.length === 0 ? (
        <p className="text-[12px] text-text-muted">No supporting documents on this claim.</p>
      ) : (
        <ul className="space-y-2">
          {ids.map((id) => (
            <li
              key={id}
              className="flex items-center gap-2 rounded-lg border border-border bg-surface-raised px-2 py-2 text-[12px]"
            >
              <FileText className="h-4 w-4 shrink-0 text-text-faint" />
              <span className="min-w-0 flex-1 truncate font-mono text-[11px] text-text" title={id}>
                {id}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

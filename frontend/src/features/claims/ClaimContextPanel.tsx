import type { ClaimAssessmentResponse } from "../../api/types/assessment";
import type { ClaimInput } from "../../api/types/claim";
import { Card } from "../../components/ui/Card";
import { ClaimAttachmentsList } from "./ClaimAttachmentsList";

export function ClaimContextPanel({
  claim,
  assessment,
}: {
  claim: ClaimInput;
  assessment: ClaimAssessmentResponse | null;
}) {
  void assessment;

  return (
    <Card className="h-fit p-4 xl:sticky xl:top-4">
      <ClaimAttachmentsList claim={claim} />
    </Card>
  );
}

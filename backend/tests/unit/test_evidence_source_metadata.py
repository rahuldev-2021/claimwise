from datetime import datetime, timezone

from app.modules.rag.citation_manager import CitationManager
from app.modules.rag.metadata_extractor import extract_metadata
from app.modules.rag.schemas import RetrievalStrategy
from app.schemas.repair_document import DocumentType, RepairDocument, VerificationStatus


class _Hit:
    def __init__(self, metadata: dict, text: str = "sample"):
        self.chunk_id = "DOC-1::0"
        self.document_id = "DOC-1"
        self.text = text
        self.score = 0.9
        self.rank = 1
        self.metadata = metadata


def test_metadata_and_citation_carry_source_type():
    doc = RepairDocument(
        document_id="DOC-1",
        document_type=DocumentType.REPAIR_MANUAL,
        title="Manual",
        content="Brake service procedure for front pads.",
        verification_status=VerificationStatus.VERIFIED,
        evidence_scope="global",
        created_at=datetime.now(timezone.utc),
    )
    meta = extract_metadata(doc)
    assert meta["evidence_scope"] == "global"
    assert meta["evidence_source_type"] == "GLOBAL_KNOWLEDGE"

    claim_doc = doc.model_copy(
        update={
            "evidence_scope": "claim",
            "claim_id": "CLM-9",
            "org_id": "org-9",
            "verification_status": VerificationStatus.PENDING,
        }
    )
    claim_meta = extract_metadata(claim_doc)
    assert claim_meta["evidence_source_type"] == "CLAIM_UPLOAD"

    mgr = CitationManager()
    result = mgr.build_result(
        query="brakes",
        strategy=RetrievalStrategy.HYBRID,
        hits=[_Hit(claim_meta)],
    )
    passage = result.passages[0]
    assert passage.evidence_source_type == "CLAIM_UPLOAD"
    assert passage.evidence_scope == "claim"
    assert passage.verification_status == "PENDING"

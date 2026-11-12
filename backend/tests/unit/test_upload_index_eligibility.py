from datetime import datetime, timezone

from app.modules.rag.upload_index_eligibility import (
    IndexAction,
    assess_claim_upload_for_index,
)
from app.schemas.repair_document import (
    DocumentType,
    RepairDocument,
    VectorIndexStatus,
    VerificationStatus,
)


def _doc(**overrides) -> RepairDocument:
    base = dict(
        document_id="DOC-UPL-1",
        claim_id="CLM-1",
        org_id="org-1",
        evidence_scope="claim",
        document_type=DocumentType.TECHNICIAN_REPORT,
        title="report.pdf",
        content="Brake pad wear measured at 2mm. Technician recommends replacement.",
        verification_status=VerificationStatus.PENDING,
        created_at=datetime.now(timezone.utc),
    )
    base.update(overrides)
    return RepairDocument(**base)


def test_skip_short_content():
    doc = _doc(content="too short")
    result = assess_claim_upload_for_index(
        doc, claim_id="CLM-1", org_id="org-1", min_text_chars=40, vector_store_has_document=False
    )
    assert result.action == IndexAction.SKIP
    assert "shorter than minimum" in result.reason


def test_skip_wrong_claim():
    doc = _doc(claim_id="CLM-OTHER")
    result = assess_claim_upload_for_index(
        doc, claim_id="CLM-1", org_id="org-1", min_text_chars=40, vector_store_has_document=False
    )
    assert result.action == IndexAction.SKIP
    assert "claim_id" in result.reason


def test_skip_already_indexed_same_fingerprint():
    doc = _doc(
        vector_index_status=VectorIndexStatus.INDEXED,
        content_fingerprint="abc",
    )
    from app.modules.rag.upload_index_eligibility import content_fingerprint

    fp = content_fingerprint(doc.content)
    doc = doc.model_copy(update={"content_fingerprint": fp})
    result = assess_claim_upload_for_index(
        doc, claim_id="CLM-1", org_id="org-1", min_text_chars=40, vector_store_has_document=True
    )
    assert result.action == IndexAction.SKIP
    assert "already indexed" in result.reason


def test_reindex_when_content_changed():
    doc = _doc(
        vector_index_status=VectorIndexStatus.INDEXED,
        content_fingerprint="stale-fingerprint",
    )
    result = assess_claim_upload_for_index(
        doc, claim_id="CLM-1", org_id="org-1", min_text_chars=40, vector_store_has_document=True
    )
    assert result.action == IndexAction.REINDEX

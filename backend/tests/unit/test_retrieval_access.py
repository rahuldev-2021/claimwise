from app.modules.rag.retrieval_access import (
    RetrievalAccessContext,
    chunk_visible_to_requester,
    filter_hits_by_scope,
)


class _Hit:
    def __init__(self, metadata: dict):
        self.metadata = metadata
        self.chunk_id = metadata.get("chunk_id", "x")
        self.document_id = metadata.get("document_id", "d")


def test_global_visible_without_access():
    meta = {"evidence_scope": "global", "document_id": "DOC-001"}
    assert chunk_visible_to_requester(meta, None)


def test_claim_scoped_requires_matching_access():
    meta = {
        "evidence_scope": "claim",
        "org_id": "org_a",
        "claim_id": "CLM-1",
    }
    access = RetrievalAccessContext(org_id="org_a", claim_id="CLM-1")
    assert chunk_visible_to_requester(meta, access)
    assert not chunk_visible_to_requester(meta, RetrievalAccessContext("org_b", "CLM-1"))
    assert not chunk_visible_to_requester(meta, RetrievalAccessContext("org_a", "CLM-2"))
    assert not chunk_visible_to_requester(meta, None)


def test_missing_scope_fails_closed():
    assert not chunk_visible_to_requester({}, None)
    assert not chunk_visible_to_requester({"document_id": "x"}, None)


def test_filter_hits_drops_foreign_claim():
    hits = [
        _Hit({"evidence_scope": "global", "document_id": "DOC-1"}),
        _Hit(
            {
                "evidence_scope": "claim",
                "org_id": "org_a",
                "claim_id": "CLM-2",
                "document_id": "DOC-u",
            }
        ),
    ]
    kept = filter_hits_by_scope(hits, RetrievalAccessContext("org_a", "CLM-1"))
    assert len(kept) == 1
    assert kept[0].document_id == "DOC-1"

from app.modules.rag.schemas import RetrievalMode


def test_ingest_sample_corpus(indexed_rag):
    health = indexed_rag.health()
    assert health.indexed
    assert health.chunk_count > 0
    assert health.document_count >= 9


def test_semantic_search_brake_noise(indexed_rag):
    result = indexed_rag.search(
        "squealing noise front wheels when braking brake pad",
        top_k=5,
        mode=RetrievalMode.ADVANCED,
    )
    assert result.passages
    assert any(
        p.document_id == "DOC-002" or "brake" in p.text.lower()
        for p in result.passages
    )


def test_hybrid_retrieve_for_claim_clm002(indexed_rag):
    result = indexed_rag.retrieve_for_claim_id("CLM-002", top_k=5)
    assert result.passages
    assert result.query
    assert any(p.document_id for p in result.passages)
    assert all(p.chunk_id and p.title for p in result.passages if p.document_id == "DOC-002")


def test_lexical_part_number(indexed_rag):
    hits = indexed_rag._lexical.retrieve("HL3Z-2001-D", top_k=3)
    assert hits
    doc_ids = {h.document_id for h in hits}
    assert "DOC-002" in doc_ids


def test_evaluation_runs(indexed_rag):
    report = indexed_rag.run_evaluation(k=3)
    assert report.dataset_size == 10
    assert len(report.summaries) == 3
    strategies = {s.strategy for s in report.summaries}
    assert strategies == {"semantic", "lexical", "hybrid"}

from app.modules.rag.lexical_retriever import BM25Retriever


def test_bm25_part_number_match():
    bm25 = BM25Retriever()
    chunk_ids = ["c1", "c2", "c3"]
    texts = [
        "Front brake pad thickness measured at 1.2mm. Part HL3Z-2001-D.",
        "Engine timing chain noise during cold start.",
        "Cooling system pressure test normal.",
    ]
    metas = [
        {"document_id": "DOC-002"},
        {"document_id": "DOC-001"},
        {"document_id": "DOC-003"},
    ]
    bm25.build(chunk_ids, texts, metas)
    hits = bm25.retrieve("HL3Z-2001-D", top_k=2)
    assert hits
    assert hits[0].document_id == "DOC-002"

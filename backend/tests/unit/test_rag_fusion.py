from app.modules.rag.fusion import RankedItem, reciprocal_rank_fusion


def test_rrf_deduplicates_and_orders():
    list_a = [
        RankedItem(chunk_id="c1", rank=1, score=0.9, document_id="d1", text="a"),
        RankedItem(chunk_id="c2", rank=2, score=0.8, document_id="d1", text="b"),
    ]
    list_b = [
        RankedItem(chunk_id="c2", rank=1, score=5.0, document_id="d1", text="b"),
        RankedItem(chunk_id="c3", rank=2, score=4.0, document_id="d2", text="c"),
    ]
    fused = reciprocal_rank_fusion([list_a, list_b], k=60)
    ids = [item.chunk_id for item in fused]
    assert ids[0] == "c2"
    assert len(ids) == 3

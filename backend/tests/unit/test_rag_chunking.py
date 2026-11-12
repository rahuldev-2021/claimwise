from app.modules.rag.chunking import ChunkingConfig, RecursiveChunker


def test_stable_chunk_ids():
    chunker = RecursiveChunker(ChunkingConfig(chunk_size=80, chunk_overlap=10))
    text = "Sentence one. " * 20
    meta = {"document_id": "DOC-T"}
    chunks = chunker.chunk_document("DOC-T", text, meta)
    assert chunks
    assert chunks[0].chunk_id == "DOC-T::chunk-0000"
    assert all(c.metadata.get("document_id") == "DOC-T" for c in chunks)


def test_short_document_no_parent_text():
    chunker = RecursiveChunker()
    chunks = chunker.chunk_document("DOC-S", "Short technician note.", {"document_id": "DOC-S"})
    assert len(chunks) == 1
    assert chunks[0].parent_text is None

from app.core.config import Settings
from app.services.rag_service import RAGService


def test_ensure_startup_corpus_idempotent_after_full_ingest():
    settings = Settings(APP_ENV="test")
    rag = RAGService.for_tests(settings)
    first = rag.ingest(force_reindex=False)
    assert first.indexed >= 1
    assert rag._lexical.is_built

    second = rag.ensure_startup_corpus()
    assert second is None


def test_ensure_startup_corpus_rebuilds_bm25_when_chroma_persisted():
    settings = Settings(APP_ENV="test")
    rag = RAGService.for_tests(settings)
    rag.ingest(force_reindex=False)
    assert rag._store.count() > 0

    rag._lexical._built = False
    rag._lexical._bm25 = None
    report = rag.ensure_startup_corpus()
    assert report is None
    assert rag._lexical.is_built

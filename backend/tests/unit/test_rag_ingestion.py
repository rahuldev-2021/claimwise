from datetime import datetime, timezone

from app.modules.rag.runtime import create_chroma_client
from app.modules.rag.schemas import IngestStatus
from app.modules.rag.vector_store import ChromaVectorStore
from app.modules.rag.ingestion import IngestionPipeline
from app.modules.rag.lexical_retriever import BM25Retriever
from app.modules.rag.embedding_provider import DeterministicEmbeddingProvider
from app.schemas.repair_document import DocumentType, RepairDocument, VerificationStatus


def _doc(document_id: str, content: str) -> RepairDocument:
    return RepairDocument(
        document_id=document_id,
        document_type=DocumentType.TECHNICIAN_REPORT,
        title="Test",
        content=content,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        verification_status=VerificationStatus.VERIFIED,
    )


def test_ingest_skips_empty_and_duplicates():
    client = create_chroma_client(persist_dir=None)
    embeddings = DeterministicEmbeddingProvider()
    store = ChromaVectorStore(client, collection_name="test_ingest", embedding_dimension=32)
    lexical = BM25Retriever()
    pipeline = IngestionPipeline(embeddings=embeddings, store=store, lexical=lexical)

    report = pipeline.ingest(
        [_doc("D1", "Brake pad wear inspection with HL3Z-2001-D reference.")]
    )
    assert report.indexed == 1

    report2 = pipeline.ingest([_doc("D1", "Brake pad wear inspection with HL3Z-2001-D reference.")])
    assert report2.skipped_duplicate == 1

    report3 = pipeline.ingest(
        [_doc("D1", "Updated brake content HL3Z-2001-D.")],
        force_reindex=True,
    )
    assert report3.indexed == 1
    assert any(r.status == IngestStatus.INDEXED for r in report3.records)

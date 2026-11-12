"""Document ingestion pipeline.

Orchestrates the full path from raw ``RepairDocument`` objects to an indexed,
searchable corpus:

    documents
      -> clean text
      -> extract scalar metadata
      -> chunk (recursive, structure-aware)
      -> embed (shared EmbeddingProvider)
      -> upsert into vector store
      -> rebuild BM25 lexical index
      -> maintain parent-text map
      -> produce an IngestReport

Behaviour
---------
* **Deduplication** — a document already present in the vector store is
  skipped (``SKIPPED_DUPLICATE``) so re-running ingestion is idempotent and
  does not double-count chunks.
* **Empty documents** — blank content yields ``SKIPPED_EMPTY``.
* **Errors** — a per-document failure is recorded as ``ERROR`` with the
  message; it does not abort the rest of the run.
* **Parent map** — for long documents, the parent window for each child chunk
  is kept in an in-memory map (not the vector store) for parent-child
  retrieval.
"""

import logging

from app.modules.rag.chunking import RecursiveChunker
from app.modules.rag.document_cleaner import clean_text, is_blank
from app.modules.rag.embedding_provider import EmbeddingProvider
from app.modules.rag.lexical_retriever import BM25Retriever
from app.modules.rag.metadata_extractor import extract_metadata
from app.modules.rag.schemas import (
    IngestReport,
    IngestStatus,
    IngestedDocumentRecord,
)
from app.modules.rag.vector_store import VectorStore
from app.schemas.repair_document import RepairDocument

logger = logging.getLogger(__name__)


def _append_searchable_metadata(
    text: str,
    doc: RepairDocument,
    metadata: dict[str, object],
) -> str:
    """Append stable metadata tokens so BM25 can match part numbers in metadata."""
    extras: list[str] = [doc.title]
    part_number = metadata.get("part_number")
    if part_number:
        extras.append(str(part_number))
    claim_id = metadata.get("claim_id")
    if claim_id:
        extras.append(str(claim_id))
    suffix = " ".join(extras)
    return f"{text}\n{suffix}".strip()


class IngestionPipeline:
    """Ingests repair documents into the vector + lexical stores."""

    def __init__(
        self,
        *,
        embeddings: EmbeddingProvider,
        store: VectorStore,
        lexical: BM25Retriever,
        chunker: RecursiveChunker | None = None,
        parent_map: dict[str, str] | None = None,
    ) -> None:
        self._embeddings = embeddings
        self._store = store
        self._lexical = lexical
        self._chunker = chunker or RecursiveChunker()
        self._parent_map = parent_map if parent_map is not None else {}

    @property
    def parent_map(self) -> dict[str, str]:
        return self._parent_map

    def ingest(
        self,
        documents: list[RepairDocument],
        *,
        force_reindex: bool = False,
    ) -> IngestReport:
        """Ingest a batch of documents and return an aggregate report."""
        records: list[IngestedDocumentRecord] = []
        total_chunks = 0

        for doc in documents:
            record = self._ingest_one(doc, force_reindex=force_reindex)
            records.append(record)
            total_chunks += record.chunk_count

        # Rebuild the lexical index from the full corpus so BM25 statistics
        # (document frequencies) stay consistent after any additions.
        self._rebuild_lexical()

        report = IngestReport(
            total_documents=len(documents),
            indexed=sum(1 for r in records if r.status == IngestStatus.INDEXED),
            skipped_duplicate=sum(
                1 for r in records if r.status == IngestStatus.SKIPPED_DUPLICATE
            ),
            skipped_empty=sum(
                1 for r in records if r.status == IngestStatus.SKIPPED_EMPTY
            ),
            errors=sum(1 for r in records if r.status == IngestStatus.ERROR),
            total_chunks=total_chunks,
            embedding_model=self._embeddings.model_name,
            embedding_dimension=self._embeddings.dimension,
            records=records,
        )
        logger.info(
            "Ingestion complete: %d indexed, %d dup, %d empty, %d errors, %d chunks",
            report.indexed,
            report.skipped_duplicate,
            report.skipped_empty,
            report.errors,
            report.total_chunks,
        )
        return report

    def _ingest_one(
        self,
        doc: RepairDocument,
        *,
        force_reindex: bool = False,
    ) -> IngestedDocumentRecord:
        document_id = doc.document_id

        if is_blank(doc.content):
            return IngestedDocumentRecord(
                document_id=document_id, status=IngestStatus.SKIPPED_EMPTY
            )

        if force_reindex and self._store.has_document(document_id):
            self._store.delete_document(document_id)
            self._parent_map = {
                k: v for k, v in self._parent_map.items() if not k.startswith(f"{document_id}::")
            }

        if self._store.has_document(document_id):
            return IngestedDocumentRecord(
                document_id=document_id, status=IngestStatus.SKIPPED_DUPLICATE
            )

        try:
            text = clean_text(doc.content)
            metadata = extract_metadata(doc)
            text = _append_searchable_metadata(text, doc, metadata)
            chunks = self._chunker.chunk_document(document_id, text, metadata)
            if not chunks:
                return IngestedDocumentRecord(
                    document_id=document_id, status=IngestStatus.SKIPPED_EMPTY
                )

            embeddings = self._embeddings.embed_documents([c.text for c in chunks])
            self._store.upsert(chunks, embeddings)

            # Record parent windows for parent-child retrieval.
            for chunk in chunks:
                if chunk.parent_text:
                    self._parent_map[chunk.chunk_id] = chunk.parent_text

            return IngestedDocumentRecord(
                document_id=document_id,
                status=IngestStatus.INDEXED,
                chunk_count=len(chunks),
            )
        except Exception as exc:  # noqa: BLE001 — record, don't abort the run
            logger.warning("Failed to ingest %s: %s", document_id, exc)
            return IngestedDocumentRecord(
                document_id=document_id, status=IngestStatus.ERROR, error=str(exc)
            )

    def purge_document(self, document_id: str) -> bool:
        """Remove a document's chunks from the vector store and refresh BM25."""
        if not self._store.has_document(document_id):
            return False
        self._store.delete_document(document_id)
        self._parent_map = {
            k: v
            for k, v in self._parent_map.items()
            if not k.startswith(f"{document_id}::")
        }
        self._rebuild_lexical()
        return True

    def rebuild_lexical_from_store(self) -> None:
        """Rebuild the in-memory BM25 index from persisted vector-store chunks."""
        self._rebuild_lexical()

    def _rebuild_lexical(self) -> None:
        """Rebuild the BM25 index from the current vector-store corpus."""
        all_chunks = self._store.list_all()
        chunk_ids = [str(c["chunk_id"]) for c in all_chunks]
        texts = [str(c["text"]) for c in all_chunks]
        metadatas = [dict(c["metadata"]) for c in all_chunks]
        self._lexical.build(chunk_ids, texts, metadatas)

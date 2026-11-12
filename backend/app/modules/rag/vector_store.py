"""Persistent vector storage.

``ChromaVectorStore`` is the default implementation.  It stores chunk
embeddings, text and scalar metadata in a ChromaDB collection and supports
similarity search, top-K, metadata filtering, deletion and re-indexing.

Key constraints honoured here
-----------------------------
* **Explicit embeddings only.**  We always pass pre-computed vectors
  (``embeddings`` / ``query_embeddings``).  We never pass raw text to
  ChromaDB's query API, because that would make ChromaDB use its bundled
  ONNX embedding model — a different model from ours — and trigger a
  download.  All embedding is done by our ``EmbeddingProvider``.
* **Scalar metadata only.**  ChromaDB metadata values must be str / int /
  float / bool.  ``_sanitize`` drops any non-scalar or ``None`` value so a
  bad field can never break a write.
* **Cosine space.**  The collection is created with ``hnsw:space=cosine``.
  ChromaDB returns a *distance* (0 = identical, 2 = opposite); we expose a
  ``score = 1 - distance`` so higher is always more relevant.

Migration to a managed store
----------------------------
The ``VectorStore`` protocol is the seam.  To move to Vertex AI Vector
Search (or another managed DB) implement the same protocol against that
backend and inject it — no retrieval code changes.  The collection name and
embedding dimension are recorded so a managed index can be rebuilt with the
same configuration.
"""

import logging
from typing import Protocol, runtime_checkable

from app.modules.rag.schemas import VectorHit

logger = logging.getLogger(__name__)

# Metadata keys that must never be stored (ChromaDB reserves ``$``-prefixed
# keys and we keep our own bookkeeping out of the store).
_RESERVED_PREFIX = "$"


class VectorStoreError(Exception):
    """Raised when a vector-store operation fails."""


@runtime_checkable
class VectorStore(Protocol):
    """Minimal vector-store contract used by the retrievers."""

    def upsert(self, chunks: list, embeddings: list[list[float]]) -> None:
        """Insert or update chunks.

        ``embeddings`` is a parallel list to ``chunks`` (same order and
        length).  Embeddings are kept out of the ``Chunk`` model so the model
        stays a clean, serializable representation of indexed text.
        """
        ...

    def query(
        self,
        embedding: list[float],
        *,
        top_k: int = 5,
        where: dict[str, object] | None = None,
    ) -> list[VectorHit]:
        """Return the ``top_k`` most similar chunks to ``embedding``."""
        ...

    def has_document(self, document_id: str) -> bool:
        """True when at least one chunk for ``document_id`` is stored."""
        ...

    def delete_document(self, document_id: str) -> None:
        """Remove all chunks belonging to ``document_id``."""
        ...

    def list_all(self) -> list[dict[str, object]]:
        """Return every stored chunk as a dict (id, text, metadata)."""
        ...

    def count(self) -> int:
        """Number of stored chunks."""
        ...

    def clear(self) -> None:
        """Delete the collection and all its data."""
        ...


def _sanitize_metadata(metadata: dict[str, object]) -> dict[str, object]:
    """Keep only scalar, non-None, non-reserved metadata values."""
    clean: dict[str, object] = {}
    for key, value in metadata.items():
        if key.startswith(_RESERVED_PREFIX):
            continue
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            clean[key] = value
        else:
            # Coerce simple enums / other scalars to their string form rather
            # than silently dropping them.
            clean[key] = str(value)
    return clean


class ChromaVectorStore:
    """ChromaDB-backed vector store using explicit embeddings."""

    def __init__(
        self,
        client: object,
        collection_name: str = "claimwise_rag",
        embedding_dimension: int = 384,
    ) -> None:
        self._client = client
        self._collection_name = collection_name
        self._embedding_dimension = embedding_dimension
        self._collection = self._get_or_create()

    def _get_or_create(self) -> object:
        try:
            return self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as exc:  # noqa: BLE001 — surface store errors
            raise VectorStoreError(f"Failed to open collection: {exc}") from exc

    # ── writes ────────────────────────────────────────────────────────

    def upsert(self, chunks: list, embeddings: list[list[float]]) -> None:
        if not chunks:
            return
        if len(chunks) != len(embeddings):
            raise VectorStoreError(
                "chunks and embeddings must have the same length"
            )
        ids = [c.chunk_id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [_sanitize_metadata(c.metadata) for c in chunks]
        try:
            self._collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(f"Upsert failed: {exc}") from exc

    # ── reads ─────────────────────────────────────────────────────────

    def query(
        self,
        embedding: list[float],
        *,
        top_k: int = 5,
        where: dict[str, object] | None = None,
    ) -> list[VectorHit]:
        if top_k <= 0:
            return []
        try:
            kwargs: dict[str, object] = {
                "query_embeddings": [embedding],
                "n_results": top_k,
                "include": ["documents", "metadatas", "distances"],
            }
            if where:
                kwargs["where"] = where
            result = self._collection.query(**kwargs)
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(f"Query failed: {exc}") from exc

        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        dists = result.get("distances", [[]])[0]

        hits: list[VectorHit] = []
        for rank, (chunk_id, doc, meta, dist) in enumerate(
            zip(ids, docs, metas, dists), start=1
        ):
            hits.append(
                VectorHit(
                    chunk_id=chunk_id,
                    document_id=str(meta.get("document_id", "")),
                    text=doc or "",
                    score=round(1.0 - float(dist), 6),
                    rank=rank,
                    metadata=dict(meta or {}),
                )
            )
        return hits

    def has_document(self, document_id: str) -> bool:
        try:
            existing = self._collection.get(where={"document_id": document_id})
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(f"has_document failed: {exc}") from exc
        return len(existing.get("ids", [])) > 0

    def delete_document(self, document_id: str) -> None:
        try:
            self._collection.delete(where={"document_id": document_id})
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(f"delete_document failed: {exc}") from exc

    def list_all(self) -> list[dict[str, object]]:
        try:
            result = self._collection.get(include=["documents", "metadatas"])
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(f"list_all failed: {exc}") from exc
        ids = result.get("ids", [])
        docs = result.get("documents", [])
        metas = result.get("metadatas", [])
        return [
            {"chunk_id": cid, "text": doc, "metadata": dict(meta or {})}
            for cid, doc, meta in zip(ids, docs, metas)
        ]

    def count(self) -> int:
        try:
            return int(self._collection.count())
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(f"count failed: {exc}") from exc

    def clear(self) -> None:
        try:
            self._client.delete_collection(self._collection_name)
        except Exception:  # noqa: BLE001 — collection may not exist
            pass
        self._collection = self._get_or_create()

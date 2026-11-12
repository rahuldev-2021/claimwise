"""Semantic (vector) retrieval.

Embeds the query with the shared ``EmbeddingProvider`` and runs a top-K
similarity search against the vector store.  This is the "basic RAG" path.
"""

from app.modules.rag.embedding_provider import EmbeddingProvider
from app.modules.rag.schemas import VectorHit
from app.modules.rag.vector_store import VectorStore


class SemanticRetriever:
    """Retrieves chunks by embedding similarity."""

    def __init__(self, embeddings: EmbeddingProvider, store: VectorStore) -> None:
        self._embeddings = embeddings
        self._store = store

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        where: dict[str, object] | None = None,
    ) -> list[VectorHit]:
        """Embed ``query`` and return the top-K similar chunks.

        Returns an empty list for a blank query (no silent failure — the
        caller decides how to surface "no results").
        """
        if not query or not query.strip():
            return []
        embedding = self._embeddings.embed_query(query)
        return self._store.query(embedding, top_k=top_k, where=where)

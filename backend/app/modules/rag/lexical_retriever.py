"""BM25 lexical retrieval.

Complements semantic search for cases where exact tokens matter: part
numbers (``BR3Z-6268-A``), diagnostic fault codes (``P0301``), and specific
technical phrases.  BM25 is a classic term-frequency / inverse-document-
frequency ranker — fast, deterministic, and explainable.

The index is built in memory from the chunk corpus at ingestion time and
rebuilt whenever the corpus changes.  It is intentionally kept separate from
the vector store so the two retrieval methods can be compared and fused
independently.
"""

import re

from app.modules.rag.schemas import LexicalHit

# Tokenizer: lowercase alphanumeric runs, keeping hyphens/digits so part
# numbers and fault codes survive as single tokens.
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-/][a-z0-9]+)*")


def tokenize(text: str) -> list[str]:
    """Lowercase and split into searchable tokens.

    ``BR3Z-6268-A`` -> ``["br3z-6268-a"]``; ``P0301`` -> ``["p0301"]``.
    """
    return _TOKEN_RE.findall(text.lower())


class BM25Retriever:
    """In-memory BM25 index over the chunk corpus."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self._k1 = k1
        self._b = b
        self._corpus: list[list[str]] = []
        self._chunk_ids: list[str] = []
        self._texts: list[str] = []
        self._metadatas: list[dict[str, object]] = []
        self._bm25: object | None = None
        self._built = False

    @property
    def is_built(self) -> bool:
        return self._built

    def build(
        self,
        chunk_ids: list[str],
        texts: list[str],
        metadatas: list[dict[str, object]],
    ) -> None:
        """(Re)build the index from the full chunk corpus."""
        try:
            from rank_bm25 import BM25Okapi
        except ImportError as exc:  # pragma: no cover - env guard
            raise RuntimeError(
                "rank_bm25 is not installed. Install it with: pip install rank_bm25"
            ) from exc

        self._chunk_ids = list(chunk_ids)
        self._texts = list(texts)
        self._metadatas = list(metadatas)
        self._corpus = [tokenize(t) for t in texts]

        if not self._corpus or all(len(c) == 0 for c in self._corpus):
            self._bm25 = None
            self._built = True
            return

        # BM25Okapi needs at least one non-empty document.
        self._bm25 = BM25Okapi(self._corpus, k1=self._k1, b=self._b)
        self._built = True

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        where: dict[str, object] | None = None,
    ) -> list[LexicalHit]:
        """Return the top-K chunks by BM25 score for ``query``.

        ``where`` is an optional metadata filter applied *after* scoring (the
        in-memory index has no native filter).  Chunks that do not match the
        filter are dropped before ranking is finalized.
        """
        if not self._built or self._bm25 is None:
            return []
        tokens = tokenize(query)
        if not tokens:
            return []

        scores = list(self._bm25.get_scores(tokens))  # type: ignore[union-attr]
        if tokens and (not scores or max(scores) <= 0.0):
            # BM25 idf can vanish on very small corpora; fall back to token overlap.
            scores = [
                float(sum(1 for token in tokens if token in set(doc)))
                for doc in self._corpus
            ]
        # Pair each chunk with its score, apply the metadata filter, then rank.
        candidates: list[tuple[float, int]] = []
        for idx, score in enumerate(scores):
            if score <= 0:
                continue
            if where and not _matches(self._metadatas[idx], where):
                continue
            candidates.append((float(score), idx))

        candidates.sort(key=lambda pair: pair[0], reverse=True)
        hits: list[LexicalHit] = []
        for rank, (score, idx) in enumerate(candidates[:top_k], start=1):
            hits.append(
                LexicalHit(
                    chunk_id=self._chunk_ids[idx],
                    document_id=str(self._metadatas[idx].get("document_id", "")),
                    text=self._texts[idx],
                    score=round(score, 6),
                    rank=rank,
                    metadata=dict(self._metadatas[idx]),
                )
            )
        return hits

    def __len__(self) -> int:
        return len(self._chunk_ids)


def _matches(metadata: dict[str, object], where: dict[str, object]) -> bool:
    """Evaluate a flat equality ``where`` clause against a metadata dict.

    Supports the simple ``{field: value}`` form and ChromaDB-style operators
    ``$in`` / ``$eq``.  A field absent from the metadata fails the filter
    (we never fabricate metadata).
    """
    for key, condition in where.items():
        if isinstance(condition, dict):
            if "$in" in condition:
                if metadata.get(key) not in condition["$in"]:
                    return False
            elif "$eq" in condition:
                if metadata.get(key) != condition["$eq"]:
                    return False
            else:
                return False
        else:
            if metadata.get(key) != condition:
                return False
    return True

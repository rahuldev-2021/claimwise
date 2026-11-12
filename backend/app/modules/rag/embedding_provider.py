"""Embedding provider abstraction.

The retrieval pipeline depends only on the ``EmbeddingProvider`` protocol, so
the concrete model can be swapped (e.g. for Google Vertex AI embeddings in a
later phase) without touching retrieval code.

``SentenceTransformerEmbeddingProvider`` is the default local implementation.
It loads the model lazily on first use so that importing the module (and
starting the API) never triggers a model download or load.  Document and query
embeddings always come from the same model instance, guaranteeing compatible
dimensions.
"""

import hashlib
import logging
import math
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)

_KNOWN_MODEL_DIMENSIONS: dict[str, int] = {
    "all-MiniLM-L6-v2": 384,
    "all-MiniLM-L12-v2": 384,
    "paraphrase-MiniLM-L6-v2": 384,
}


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Converts text into fixed-dimension vectors."""

    @property
    def model_name(self) -> str:
        """Identifier for the embedding model (used for versioning)."""
        ...

    @property
    def dimension(self) -> int:
        """Vector dimensionality produced by this provider."""
        ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of document texts."""
        ...

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query text (same space as documents)."""
        ...


class SentenceTransformerEmbeddingProvider:
    """Local embedding provider backed by a sentence-transformers model.

    * Lazy loading — the model is loaded on the first ``embed_*`` call.
    * L2-normalized embeddings so cosine similarity == dot product.
    * Batching — ``embed_documents`` processes in ``batch_size`` groups.
    * Records model name and dimension for versioned re-indexing.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = "cpu",
        batch_size: int = 32,
    ) -> None:
        self._model_name = model_name
        self._device = device
        self._batch_size = batch_size
        self._model: object | None = None
        self._dim: int | None = None

    def _load(self) -> object:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:  # pragma: no cover - env guard
                raise EmbeddingError(
                    "sentence-transformers is not installed. "
                    "Install it with: pip install sentence-transformers"
                ) from exc
            logger.info("Loading embedding model %s on %s", self._model_name, self._device)
            try:
                self._model = SentenceTransformer(self._model_name, device=self._device)
            except Exception as exc:  # noqa: BLE001 — surface load failure
                raise EmbeddingError(f"Failed to load model {self._model_name}: {exc}") from exc
            self._dim = int(self._model.get_embedding_dimension())
        return self._model

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        if self._dim is None:
            self._dim = _KNOWN_MODEL_DIMENSIONS.get(self._model_name, 384)
        return self._dim

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._load()
        vectors = model.encode(  # type: ignore[union-attr]
            texts,
            batch_size=self._batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [list(map(float, row)) for row in vectors]

    def embed_query(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise EmbeddingError("Query text must not be blank")
        model = self._load()
        vector = model.encode(  # type: ignore[union-attr]
            text,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return list(map(float, vector))


class DeterministicEmbeddingProvider:
    """Hash-based embeddings for tests (fixed dimension, no model download)."""

    def __init__(self, *, dimension: int = 32, model_name: str = "deterministic-hash-v1") -> None:
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        self._dimension = dimension
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    def _embed_one(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        index = 0
        while len(values) < self._dimension:
            chunk = digest[index : index + 4]
            if len(chunk) < 4:
                digest = hashlib.sha256(digest).digest()
                index = 0
                chunk = digest[index : index + 4]
            index += 4
            raw = int.from_bytes(chunk, "big", signed=False)
            values.append((raw / 2**32) * 2.0 - 1.0)
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise EmbeddingError("Query text must not be blank")
        return self._embed_one(text)

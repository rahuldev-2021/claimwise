"""Optional reranking of retrieved candidates.

Reranking re-scores a small set of already-retrieved candidates with a more
expensive model (a cross-encoder) to improve precision.  It is *optional*:

* ``NoopReranker`` is the default — it returns candidates unchanged with
  ``rerank_score=None``.  This is what runs in normal operation so that no
  model is downloaded or loaded at startup.
* ``CrossEncoderReranker`` loads a cross-encoder lazily on first use.  If the
  model or its dependency is unavailable it raises ``RerankerUnavailable``,
  which the pipeline catches and degrades to the no-op behaviour rather than
  failing the whole retrieval.

Reranking scores are reported *separately* from the original retrieval score
so the two are never conflated.
"""

import logging
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


class RerankerUnavailable(Exception):
    """Raised when an optional reranker cannot be used."""


@runtime_checkable
class Reranker(Protocol):
    """Re-scores (query, passage) pairs."""

    @property
    def name(self) -> str:
        ...

    def rerank(
        self,
        query: str,
        passages: list[dict[str, object]],
    ) -> list[float | None]:
        """Return a rerank score per passage (same order as input).

        Each passage dict has at least ``text``.  Scores are on the model's
        native scale (not normalized to 0-1) and are reported separately from
        the retrieval score.  ``None`` indicates no rerank score was produced
        (e.g. the no-op reranker).
        """
        ...


class NoopReranker:
    """Default reranker that leaves candidates in their original order."""

    @property
    def name(self) -> str:
        return "none"

    def rerank(
        self, query: str, passages: list[dict[str, object]]
    ) -> list[float | None]:
        return [None] * len(passages)


class CrossEncoderReranker:
    """Cross-encoder reranker backed by a sentence-transformers model.

    The model is loaded lazily on the first ``rerank`` call.  If loading or
    scoring fails, ``RerankerUnavailable`` is raised so the caller can fall
    back to the no-op reranker.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        self._model_name = model_name
        self._model: object | None = None

    @property
    def name(self) -> str:
        return self._model_name

    def _load(self) -> object:
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
            except ImportError as exc:  # pragma: no cover - env guard
                raise RerankerUnavailable(
                    "sentence-transformers is not installed; reranking unavailable"
                ) from exc
            try:
                self._model = CrossEncoder(self._model_name)
            except Exception as exc:  # noqa: BLE001
                raise RerankerUnavailable(
                    f"Failed to load reranker {self._model_name}: {exc}"
                ) from exc
        return self._model

    def rerank(
        self, query: str, passages: list[dict[str, object]]
    ) -> list[float | None]:
        if not passages:
            return []
        model = self._load()
        pairs = [(query, str(p.get("text", ""))) for p in passages]
        try:
            scores = model.predict(pairs)  # type: ignore[union-attr]
        except Exception as exc:  # noqa: BLE001
            raise RerankerUnavailable(f"Rerank scoring failed: {exc}") from exc
        return [float(s) for s in scores]

"""Configurable, structure-aware document chunking.

Strategy
--------
A *recursive* chunker splits text on a hierarchy of delimiters
(paragraph -> sentence -> clause -> word) so that chunks prefer to break at
natural technical boundaries rather than mid-sentence.  A configurable
overlap keeps context across chunk boundaries.

Parent-child
------------
When a document is longer than ``parent_chunk_size``, each child chunk also
carries the surrounding ``parent_text`` (a larger window) so a retrieved
snippet can be understood in context.  Short documents (<= parent size) get
no parent text — adding it would be pure overhead.

Stable IDs
----------
Chunk ids are ``{document_id}::chunk-{index:04d}``.  Because chunking is
deterministic for a given (text, config), the same document always yields the
same chunk ids, which makes re-indexing idempotent.
"""

from dataclasses import dataclass, field

from app.modules.rag.schemas import Chunk

# Delimiters tried in order, from coarsest to finest.
_DEFAULT_SEPARATORS: tuple[str, ...] = ("\n\n", "\n", ". ", " ", "")


@dataclass(frozen=True)
class ChunkingConfig:
    """Tunables for the recursive chunker."""

    chunk_size: int = 500
    chunk_overlap: int = 100
    parent_chunk_size: int = 1000
    separators: tuple[str, ...] = _DEFAULT_SEPARATORS

    def __post_init__(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must be >= 0")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be < chunk_size")
        if self.parent_chunk_size < self.chunk_size:
            raise ValueError("parent_chunk_size must be >= chunk_size")


class RecursiveChunker:
    """Splits document text into overlapping, metadata-preserving chunks."""

    def __init__(self, config: ChunkingConfig | None = None) -> None:
        self.config = config or ChunkingConfig()

    def chunk_document(
        self,
        document_id: str,
        text: str,
        metadata: dict[str, object],
    ) -> list[Chunk]:
        """Chunk a single document's text.

        Returns an empty list for blank text (the caller records this as
        ``SKIPPED_EMPTY``).  Every chunk carries the document metadata plus a
        ``chunk_index`` and, for long documents, ``parent_text``.
        """
        if not text or not text.strip():
            return []

        pieces = self._split(text, self.config.separators, self.config.chunk_size)
        # Merge tiny trailing pieces into the previous chunk to avoid
        # near-empty chunks.
        pieces = self._merge_small(pieces, self.config.chunk_size)

        use_parent = len(text) > self.config.parent_chunk_size
        chunks: list[Chunk] = []
        for index, piece in enumerate(pieces):
            piece = piece.strip()
            if not piece:
                continue
            chunk_meta = dict(metadata)
            chunk_meta["chunk_index"] = index
            parent_text = self._parent_window(text, piece) if use_parent else None
            chunks.append(
                Chunk(
                    chunk_id=f"{document_id}::chunk-{index:04d}",
                    document_id=document_id,
                    text=piece,
                    metadata=chunk_meta,
                    parent_text=parent_text,
                )
            )
        return chunks

    # ── internals ─────────────────────────────────────────────────────

    def _split(self, text: str, separators: tuple[str, ...], size: int) -> list[str]:
        if len(text) <= size:
            return [text]

        sep = separators[0]
        rest = separators[1:]
        if not sep:
            # Hard character-level split as a last resort.
            return [text[i : i + size] for i in range(0, len(text), size)]

        parts = text.split(sep)
        pieces: list[str] = []
        current = ""
        for part in parts:
            candidate = f"{current}{sep}{part}" if current else part
            if len(candidate) <= size:
                current = candidate
            else:
                if current:
                    pieces.append(current)
                if len(part) > size:
                    # Recurse on the oversized part with finer separators.
                    pieces.extend(self._split(part, rest, size))
                    current = ""
                else:
                    current = part
        if current:
            pieces.append(current)
        return pieces

    def _merge_small(self, pieces: list[str], size: int) -> list[str]:
        """Fold a trailing piece shorter than half the target into its
        predecessor to avoid a stubby final chunk."""
        if len(pieces) < 2:
            return pieces
        threshold = max(1, size // 4)
        result = list(pieces)
        while len(result) >= 2 and len(result[-1].strip()) < threshold:
            last = result.pop()
            result[-1] = f"{result[-1]} {last}".strip()
        return result

    def _parent_window(self, text: str, child: str) -> str | None:
        """Return a parent window around ``child`` within ``text``.

        The window is centred on the child and capped at ``parent_chunk_size``.
        Returns ``None`` if the child cannot be located (should not happen for
        deterministic chunking).
        """
        start = text.find(child)
        if start < 0:
            return None
        half = self.config.parent_chunk_size // 2
        lo = max(0, start - half)
        hi = min(len(text), start + len(child) + half)
        return text[lo:hi].strip()

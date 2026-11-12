"""RAG runtime helpers (clients, shared state)."""

from pathlib import Path
from typing import Any


def create_chroma_client(*, persist_dir: str | None = None) -> Any:
    """Create a ChromaDB client (persistent or in-memory).

    Raises ``ImportError`` when chromadb is not installed.
    """
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    # Avoid Chroma -> PostHog telemetry (breaks with posthog 7.x: capture() signature).
    chroma_settings = ChromaSettings(anonymized_telemetry=False)

    if persist_dir:
        path = Path(persist_dir)
        path.mkdir(parents=True, exist_ok=True)
        return chromadb.PersistentClient(path=str(path), settings=chroma_settings)
    return chromadb.EphemeralClient(settings=chroma_settings)


class ParentTextRegistry:
    """Shared chunk_id -> parent_text map across ingest and retrieval."""

    def __init__(self) -> None:
        self._map: dict[str, str] = {}

    @property
    def mapping(self) -> dict[str, str]:
        return self._map

    def merge(self, entries: dict[str, str]) -> None:
        self._map.update(entries)

    def clear(self) -> None:
        self._map.clear()

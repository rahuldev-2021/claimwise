"""Process-wide RAGService singleton (shared Chroma + in-memory BM25)."""

from __future__ import annotations

from threading import Lock

from app.core.config import Settings, get_settings
from app.services.rag_service import RAGService

_lock = Lock()
_instance: RAGService | None = None


def get_rag_service(settings: Settings | None = None) -> RAGService:
    global _instance
    if _instance is not None:
        return _instance
    with _lock:
        if _instance is None:
            _instance = RAGService(settings or get_settings())
    return _instance


def reset_rag_service_for_tests() -> None:
    """Clear the singleton (pytest)."""
    global _instance
    with _lock:
        _instance = None

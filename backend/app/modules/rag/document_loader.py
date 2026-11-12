"""Document loading for RAG ingestion.

Provides two entry points that both yield ``RepairDocument`` objects:

* ``from_repository`` — loads from an existing ``SampleClaimRepository``
  (reuses Phase 1 data access; no file-system work here).
* ``from_json_file`` — parses a JSON file via ``JsonDocumentParser``.

Keeping loading separate from the ingestion pipeline means the pipeline can
be tested with in-memory document lists and the repository can be swapped for
BigQuery / Cloud Storage later without changing ingestion logic.
"""

from pathlib import Path

from app.modules.rag.document_parser import JsonDocumentParser
from app.schemas.repair_document import RepairDocument


class DocumentLoader:
    """Loads repair documents from a repository or a JSON file."""

    def __init__(self, parser: JsonDocumentParser | None = None) -> None:
        self._parser = parser or JsonDocumentParser()

    def from_repository(self, repository: object) -> list[RepairDocument]:
        """Load all documents from a repository exposing ``list_documents()``."""
        documents = repository.list_documents()
        if not isinstance(documents, list):
            raise ValueError("repository.list_documents() must return a list")
        return documents

    def from_json_file(self, path: str | Path) -> list[RepairDocument]:
        """Load and parse documents from a JSON file on disk."""
        file_path = Path(path)
        if not file_path.exists():
            raise ValueError(f"Document file does not exist: {file_path}")
        text = file_path.read_text(encoding="utf-8")
        return self._parser.parse(text)

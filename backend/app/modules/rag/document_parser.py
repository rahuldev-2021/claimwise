"""Document parser abstraction.

Phase 3 ships a JSON parser for the structured ``RepairDocument`` records.
The ``DocumentParser`` protocol lets later phases add PDF / DOCX / HTML
parsers without touching the ingestion pipeline — a new parser only needs to
implement ``parse`` and return a list of ``RepairDocument``.
"""

from typing import Protocol, runtime_checkable

from app.schemas.repair_document import RepairDocument


@runtime_checkable
class DocumentParser(Protocol):
    """Converts a raw source into validated ``RepairDocument`` objects."""

    def parse(self, source: object) -> list[RepairDocument]:
        """Parse ``source`` into documents.

        Implementations must raise ``ValueError`` (or a subclass) when the
        source is structurally invalid so the ingestion pipeline can record a
        per-document error rather than crashing the whole run.
        """
        ...


class JsonDocumentParser:
    """Parses a JSON array of repair-document objects.

    Accepts either a ``list`` of raw dicts or a JSON ``str``.  Each record is
    validated against ``RepairDocument`` (which enforces non-blank
    ``document_id`` / ``title`` / ``content`` and a valid ``document_type``).
    """

    def parse(self, source: object) -> list[RepairDocument]:
        import json

        if isinstance(source, str):
            try:
                raw = json.loads(source)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON: {exc}") from exc
        elif isinstance(source, list):
            raw = source
        else:
            raise ValueError(
                "JsonDocumentParser expects a JSON string or a list of records"
            )

        if not isinstance(raw, list):
            raise ValueError("Expected a JSON array of repair documents")

        documents: list[RepairDocument] = []
        for i, item in enumerate(raw):
            try:
                documents.append(RepairDocument.model_validate(item))
            except Exception as exc:  # noqa: BLE001 — surface per-record error
                raise ValueError(f"Record {i}: {exc}") from exc
        return documents

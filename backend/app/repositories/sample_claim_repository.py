"""Repository that loads sample claims and documents from local JSON files."""

import json
import logging
from pathlib import Path
from typing import TypeVar

from app.core.exceptions import ClaimNotFoundError, DataLoadError, DocumentNotFoundError
from app.schemas.claim import ClaimInput
from app.schemas.repair_document import RepairDocument

logger = logging.getLogger(__name__)

T = TypeVar("T")


class SampleClaimRepository:
    """Reads synthetic claim and document data from JSON files on disk.

    Designed to be replaced by a BigQuery or PostgreSQL repository in
    later phases without changing the service layer.
    """

    def __init__(self, data_dir: str | Path) -> None:
        self._data_dir = Path(data_dir)
        self._claims: dict[str, ClaimInput] = {}
        self._documents: dict[str, RepairDocument] = {}
        self._load()

    def _load(self) -> None:
        self._claims = self._load_claims()
        self._documents = self._load_documents()

    def _load_claims(self) -> dict[str, ClaimInput]:
        path = self._data_dir / "claims.json"
        return {c.claim_id: c for c in self._parse_list(path, ClaimInput)}

    def _load_documents(self) -> dict[str, RepairDocument]:
        path = self._data_dir / "repair_documents.json"
        return {d.document_id: d for d in self._parse_list(path, RepairDocument)}

    @staticmethod
    def _parse_list(path: Path, model: type[T]) -> list[T]:
        if not path.exists():
            raise DataLoadError(str(path), "File does not exist")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise DataLoadError(str(path), str(exc)) from exc
        if not isinstance(raw, list):
            raise DataLoadError(str(path), "Expected a JSON array at the top level")
        results: list[T] = []
        for i, item in enumerate(raw):
            try:
                results.append(model.model_validate(item))
            except Exception as exc:
                raise DataLoadError(str(path), f"Record {i}: {exc}") from exc
        logger.info("Loaded %d records from %s", len(results), path.name)
        return results

    # ── Claims ────────────────────────────────────────────────────────

    def get_claim(self, claim_id: str) -> ClaimInput:
        try:
            return self._claims[claim_id]
        except KeyError:
            raise ClaimNotFoundError(claim_id)

    def list_claims(self) -> list[ClaimInput]:
        return list(self._claims.values())

    # ── Documents ─────────────────────────────────────────────────────

    def get_document(self, document_id: str) -> RepairDocument:
        try:
            return self._documents[document_id]
        except KeyError:
            raise DocumentNotFoundError(document_id)

    def list_documents(self) -> list[RepairDocument]:
        return list(self._documents.values())

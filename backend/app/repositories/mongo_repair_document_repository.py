"""Per-claim repair documents in MongoDB."""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from pymongo import ASCENDING
from pymongo.database import Database

from app.schemas.repair_document import RepairDocument


class MongoRepairDocumentRepository:
    COLLECTION = "repair_documents"

    def __init__(self, db: Database) -> None:
        self._col = db[self.COLLECTION]
        self._col.create_index("document_id", unique=True)
        self._col.create_index([("org_id", ASCENDING), ("claim_id", ASCENDING)])

    def insert(self, doc: RepairDocument, *, org_id: str) -> RepairDocument:
        payload = doc.model_dump(mode="json")
        payload["org_id"] = org_id
        self._col.insert_one(payload)
        return doc

    def update_fields(
        self,
        document_id: str,
        org_id: str,
        fields: dict[str, Any],
    ) -> bool:
        result = self._col.update_one(
            {"document_id": document_id, "org_id": org_id},
            {"$set": fields},
        )
        return result.matched_count > 0

    def delete(self, document_id: str, org_id: str) -> bool:
        result = self._col.delete_one({"document_id": document_id, "org_id": org_id})
        return result.deleted_count > 0

    def get(self, document_id: str, org_id: Optional[str] = None) -> Optional[RepairDocument]:
        query: dict[str, Any] = {"document_id": document_id}
        if org_id:
            query["org_id"] = org_id
        raw = self._col.find_one(query)
        if not raw:
            return None
        raw.pop("_id", None)
        raw.pop("org_id", None)
        return RepairDocument.model_validate(raw)

    def list_for_claim(self, claim_id: str, org_id: str) -> list[RepairDocument]:
        cursor = self._col.find({"claim_id": claim_id, "org_id": org_id})
        out: list[RepairDocument] = []
        for raw in cursor:
            raw.pop("_id", None)
            raw.pop("org_id", None)
            out.append(RepairDocument.model_validate(raw))
        return out

    def list_all(self) -> list[RepairDocument]:
        cursor = self._col.find({})
        out: list[RepairDocument] = []
        for raw in cursor:
            raw.pop("_id", None)
            raw.pop("org_id", None)
            out.append(RepairDocument.model_validate(raw))
        return out

    @staticmethod
    def new_document_id() -> str:
        return f"DOC-{uuid4().hex[:12].upper()}"

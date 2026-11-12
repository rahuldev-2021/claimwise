"""Approved historical repair records — MongoDB source of truth (Chroma is search-only)."""

from typing import Any

from pymongo import ASCENDING
from pymongo.database import Database

from app.schemas.historical_repair import HistoricalRepairRecord


class MongoHistoricalRepairRepository:
    COLLECTION = "historical_repairs"

    def __init__(self, db: Database) -> None:
        self._col = db[self.COLLECTION]
        self._col.create_index("historical_repair_id", unique=True)
        self._col.create_index([("repair_category", ASCENDING)])

    def upsert(self, record: HistoricalRepairRecord) -> None:
        payload = record.model_dump(mode="json")
        self._col.update_one(
            {"historical_repair_id": record.historical_repair_id},
            {"$set": payload},
            upsert=True,
        )

    def upsert_many(self, records: list[HistoricalRepairRecord]) -> int:
        count = 0
        for record in records:
            self.upsert(record)
            count += 1
        return count

    def get(self, historical_repair_id: str) -> HistoricalRepairRecord | None:
        raw = self._col.find_one({"historical_repair_id": historical_repair_id})
        if not raw:
            return None
        raw.pop("_id", None)
        return HistoricalRepairRecord.model_validate(raw)

    def list_all(self) -> list[HistoricalRepairRecord]:
        out: list[HistoricalRepairRecord] = []
        for raw in self._col.find({}):
            raw.pop("_id", None)
            out.append(HistoricalRepairRecord.model_validate(raw))
        return out

    def delete(self, historical_repair_id: str) -> bool:
        result = self._col.delete_one({"historical_repair_id": historical_repair_id})
        return result.deleted_count > 0

    def vector_purge_ids(self, historical_repair_id: str) -> dict[str, Any]:
        """Return document ids in Chroma that correspond to this historical row."""
        return {"document_id": f"HIST-{historical_repair_id}"}

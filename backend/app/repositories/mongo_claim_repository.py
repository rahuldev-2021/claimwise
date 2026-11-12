"""MongoDB persistence for submitted claims."""

from datetime import datetime, timezone
from typing import Any, Optional

from pymongo import ASCENDING, ReturnDocument
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.schemas.claim import ClaimInput
from app.schemas.persisted_claim import PersistedClaim


class MongoClaimRepository:
    COLLECTION = "claims"
    COUNTERS = "counters"

    def __init__(self, db: Database) -> None:
        self._col = db[self.COLLECTION]
        self._counters = db[self.COUNTERS]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self._col.create_index("claim_id", unique=True)
        self._col.create_index([("org_id", ASCENDING), ("claim.claim_status", ASCENDING)])
        self._col.create_index([("org_id", ASCENDING), ("created_at", ASCENDING)])
        try:
            self._counters.insert_one({"_id": "claim_seq", "seq": 0})
        except DuplicateKeyError:
            pass

    def next_claim_id(self) -> str:
        doc = self._counters.find_one_and_update(
            {"_id": "claim_seq"},
            {"$inc": {"seq": 1}},
            return_document=ReturnDocument.AFTER,
        )
        seq = int(doc["seq"])
        return f"CLM-{seq:04d}"

    def insert(self, record: PersistedClaim, session=None) -> PersistedClaim:
        data = record.model_dump(mode="json")
        data["claim_id"] = record.claim_id
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._col.insert_one(data, session=session)
        return record

    def get_by_claim_id(self, claim_id: str, org_id: Optional[str] = None) -> Optional[PersistedClaim]:
        query: dict[str, Any] = {"claim_id": claim_id}
        if org_id:
            query["org_id"] = org_id
        doc = self._col.find_one(query)
        if not doc:
            doc = self._col.find_one({"claim.claim_id": claim_id, **({"org_id": org_id} if org_id else {})})
        if not doc:
            return None
        return PersistedClaim.model_validate(self._normalize_doc(doc))

    def list_by_org(self, org_id: str) -> list[PersistedClaim]:
        cursor = self._col.find({"org_id": org_id}).sort("created_at", -1)
        return [PersistedClaim.model_validate(self._normalize_doc(d)) for d in cursor]

    def list_all_mongo(self) -> list[PersistedClaim]:
        cursor = self._col.find({}).sort("created_at", -1)
        return [PersistedClaim.model_validate(self._normalize_doc(d)) for d in cursor]

    def append_llm_recommendation(
        self,
        claim_id: str,
        org_id: str,
        record: dict[str, Any],
        *,
        history_max: int = 20,
    ) -> Optional[PersistedClaim]:
        rec_id = record.get("recommendation_id")
        push_doc = record
        doc = self._col.find_one({"claim_id": claim_id, "org_id": org_id}) or self._col.find_one(
            {"claim.claim_id": claim_id, "org_id": org_id}
        )
        if not doc:
            return None
        history = list(doc.get("llm_recommendation_executions") or [])
        history.append(push_doc)
        if len(history) > history_max:
            history = history[-history_max:]
        patch = {
            "llm_recommendation_executions": history,
            "latest_llm_recommendation_id": rec_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        query = {"_id": doc["_id"]}
        updated = self._col.find_one_and_update(
            query,
            {"$set": patch},
            return_document=ReturnDocument.AFTER,
        )
        return PersistedClaim.model_validate(self._normalize_doc(updated)) if updated else None

    def update(self, claim_id: str, org_id: str, patch: dict[str, Any]) -> Optional[PersistedClaim]:
        patch = {**patch, "updated_at": datetime.now(timezone.utc).isoformat()}
        doc = self._col.find_one_and_update(
            {"claim_id": claim_id, "org_id": org_id},
            {"$set": patch},
            return_document=ReturnDocument.AFTER,
        )
        if not doc:
            doc = self._col.find_one_and_update(
                {"claim.claim_id": claim_id, "org_id": org_id},
                {"$set": patch},
                return_document=ReturnDocument.AFTER,
            )
        return PersistedClaim.model_validate(self._normalize_doc(doc)) if doc else None

    def find_unprocessed_outbox(self, limit: int = 20) -> list[PersistedClaim]:
        cursor = self._col.find({"outbox": {"$elemMatch": {"processed": False}}}).limit(limit)
        return [PersistedClaim.model_validate(self._normalize_doc(d)) for d in cursor]

    def mark_outbox_processed(self, claim_id: str, org_id: str, job_id: str) -> None:
        self._col.update_one(
            {"claim_id": claim_id, "org_id": org_id},
            {
                "$set": {
                    "outbox.$[ev].processed": True,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            },
            array_filters=[{"ev.job_id": job_id, "ev.processed": False}],
        )

    @staticmethod
    def _normalize_doc(doc: dict[str, Any]) -> dict[str, Any]:
        out = dict(doc)
        out.pop("_id", None)
        if "claim_id" in out and "claim" in out and isinstance(out["claim"], dict):
            if "claim_id" not in out["claim"]:
                out["claim"]["claim_id"] = out["claim_id"]
        return out

    def to_claim_input(self, record: PersistedClaim) -> ClaimInput:
        return record.claim

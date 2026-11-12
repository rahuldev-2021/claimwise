"""Mongo submitted claims plus read-only sample JSON (demo / legacy)."""

from typing import Optional

from app.auth.dependencies import CurrentUser
from app.auth.org_access import can_access_org, is_super_admin
from app.core.exceptions import ClaimNotFoundError, DocumentNotFoundError
from app.repositories.mongo_claim_repository import MongoClaimRepository
from app.repositories.mongo_repair_document_repository import MongoRepairDocumentRepository
from app.repositories.sample_claim_repository import SampleClaimRepository
from app.schemas.claim import ClaimInput
from app.schemas.persisted_claim import PersistedClaim
from app.schemas.processing_status import ProcessingStatus
from app.schemas.repair_document import RepairDocument


class CompositeClaimRepository:
    def __init__(
        self,
        mongo: MongoClaimRepository,
        sample: SampleClaimRepository,
        documents: MongoRepairDocumentRepository,
    ) -> None:
        self._mongo = mongo
        self._sample = sample
        self._documents = documents

    def get_persisted(self, claim_id: str, org_id: Optional[str]) -> Optional[PersistedClaim]:
        return self._mongo.get_by_claim_id(claim_id, org_id=org_id)

    def get_persisted_for_user(self, claim_id: str, user: CurrentUser) -> Optional[PersistedClaim]:
        org_filter = None if is_super_admin(user) else user.org_id
        record = self._mongo.get_by_claim_id(claim_id, org_id=org_filter)
        if record and can_access_org(user, record.org_id):
            return record
        return None

    def update_persisted(self, claim_id: str, org_id: str, patch: dict) -> Optional[PersistedClaim]:
        return self._mongo.update(claim_id, org_id, patch)

    def append_llm_recommendation(
        self,
        claim_id: str,
        org_id: str,
        record: dict,
        *,
        history_max: int = 20,
    ) -> Optional[PersistedClaim]:
        return self._mongo.append_llm_recommendation(
            claim_id, org_id, record, history_max=history_max
        )

    def get_claim_for_user(self, claim_id: str, user: CurrentUser) -> ClaimInput:
        org_filter = None if is_super_admin(user) else user.org_id
        record = self._mongo.get_by_claim_id(claim_id, org_id=org_filter)
        if record:
            if not can_access_org(user, record.org_id):
                raise ClaimNotFoundError(claim_id)
            return record.claim
        try:
            claim = self._sample.get_claim(claim_id)
        except ClaimNotFoundError:
            raise
        if not is_super_admin(user) and org_filter:
            pass
        return claim

    def list_claims_for_user(self, user: CurrentUser) -> list[ClaimInput]:
        mongo_claims: list[ClaimInput] = []
        if is_super_admin(user):
            mongo_claims = [r.claim for r in self._mongo.list_all_mongo()]
        elif user.org_id:
            mongo_claims = [r.claim for r in self._mongo.list_by_org(user.org_id)]
        sample_ids = {c.claim_id for c in mongo_claims}
        merged = list(mongo_claims)
        for c in self._sample.list_claims():
            if c.claim_id not in sample_ids:
                merged.append(c)
        return merged

    def get_processing_status(self, claim_id: str, user: CurrentUser) -> ProcessingStatus:
        org_filter = None if is_super_admin(user) else user.org_id
        record = self._mongo.get_by_claim_id(claim_id, org_id=org_filter)
        if not record:
            raise ClaimNotFoundError(claim_id)
        if not can_access_org(user, record.org_id):
            raise ClaimNotFoundError(claim_id)
        return record.processing_status

    def get_claim(self, claim_id: str) -> ClaimInput:
        record = self._mongo.get_by_claim_id(claim_id)
        if record:
            return record.claim
        return self._sample.get_claim(claim_id)

    def list_claims(self) -> list[ClaimInput]:
        mongo_claims = [r.claim for r in self._mongo.list_all_mongo()]
        ids = {c.claim_id for c in mongo_claims}
        return mongo_claims + [c for c in self._sample.list_claims() if c.claim_id not in ids]

    def get_document(self, document_id: str) -> RepairDocument:
        doc = self._documents.get(document_id)
        if doc:
            return doc
        return self._sample.get_document(document_id)

    def list_documents(self) -> list[RepairDocument]:
        mongo_docs = self._documents.list_all()
        ids = {d.document_id for d in mongo_docs}
        return mongo_docs + [d for d in self._sample.list_documents() if d.document_id not in ids]

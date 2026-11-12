"""Claim and document access (Mongo + sample JSON)."""

from functools import lru_cache
from typing import Optional

from app.auth.dependencies import CurrentUser
from app.auth.mongodb import get_auth_db
from app.core.config import Settings, get_settings
from app.core.exceptions import ClaimNotFoundError, DocumentNotFoundError
from app.repositories.composite_claim_repository import CompositeClaimRepository
from app.repositories.mongo_claim_repository import MongoClaimRepository
from app.repositories.mongo_repair_document_repository import MongoRepairDocumentRepository
from app.repositories.sample_claim_repository import SampleClaimRepository
from app.schemas.claim import ClaimInput
from app.schemas.processing_status import ProcessingStatus
from app.schemas.repair_document import RepairDocument
from app.services.processing_status_reconcile import reconcile_processing_status


@lru_cache
def _composite_repo_for_settings_key(sample_dir: str) -> CompositeClaimRepository:
    settings = get_settings()
    db = get_auth_db(settings)
    return CompositeClaimRepository(
        MongoClaimRepository(db),
        SampleClaimRepository(data_dir=sample_dir),
        MongoRepairDocumentRepository(db),
    )


class ClaimService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._repo = _composite_repo_for_settings_key(settings.SAMPLE_DATA_DIR)

    def get_claim(self, claim_id: str) -> ClaimInput:
        try:
            return self._repo.get_claim(claim_id)
        except ClaimNotFoundError:
            raise

    def get_claim_for_user(self, claim_id: str, user: CurrentUser) -> ClaimInput:
        return self._repo.get_claim_for_user(claim_id, user)

    def list_claims(self) -> list[ClaimInput]:
        return self._repo.list_claims()

    def list_claims_for_user(self, user: CurrentUser) -> list[ClaimInput]:
        return self._repo.list_claims_for_user(user)

    def get_processing_status(self, claim_id: str, user: CurrentUser) -> ProcessingStatus:
        ps = self._repo.get_processing_status(claim_id, user)
        try:
            from app.services.rag_service_provider import get_rag_service

            rag_indexed = get_rag_service(self._settings).health().indexed
        except Exception:
            rag_indexed = False
        return reconcile_processing_status(ps, rag_indexed=rag_indexed)

    def get_document(self, document_id: str) -> RepairDocument:
        try:
            return self._repo.get_document(document_id)
        except DocumentNotFoundError:
            raise

    def list_documents(self) -> list[RepairDocument]:
        return self._repo.list_documents()

    def get_persisted_org_id(self, claim_id: str) -> Optional[str]:
        record = self._repo.get_persisted(claim_id, org_id=None)
        return record.org_id if record else None

    def get_persisted_for_user(self, claim_id: str, user: CurrentUser):
        return self._repo.get_persisted_for_user(claim_id, user)

    def get_persisted(self, claim_id: str, org_id: str | None = None):
        return self._repo.get_persisted(claim_id, org_id=org_id)

    def update_persisted(self, claim_id: str, org_id: str, patch: dict):
        return self._repo.update_persisted(claim_id, org_id, patch)

    def get_latest_assessment_for_user(
        self, claim_id: str, user: CurrentUser
    ):
        from app.schemas.claim_assessment import ClaimAssessmentResponse

        record = self.get_persisted_for_user(claim_id, user)
        if not record or not record.latest_assessment:
            return None
        if isinstance(record.latest_assessment, ClaimAssessmentResponse):
            return record.latest_assessment
        return ClaimAssessmentResponse.model_validate(record.latest_assessment)

    def append_llm_recommendation(
        self,
        claim_id: str,
        org_id: str,
        record: dict,
        *,
        history_max: int = 20,
    ):
        return self._repo.append_llm_recommendation(
            claim_id, org_id, record, history_max=history_max
        )

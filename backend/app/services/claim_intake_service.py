"""Validate submissions, persist claims, enqueue investigation jobs."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import uuid4

from pymongo.errors import OperationFailure

from app.api.schemas.claim_create import ClaimCreateRequest
from app.auth.dependencies import CurrentUser
from app.core.config import Settings
from app.jobs.mongo_job_queue import MongoJobQueue
from app.jobs.schemas import JobType
from app.modules.claim_documents.blob_store import LocalBlobStore
from app.modules.claim_documents.security import validate_upload
from app.repositories.mongo_claim_repository import MongoClaimRepository
from app.schemas.claim import ClaimInput, ClaimStatus
from app.schemas.persisted_claim import ClaimMetadata, ClaimOutboxEvent, PersistedClaim
from app.schemas.processing_status import initial_processing_status
from app.schemas.repair import Repair
from app.schemas.vehicle import Vehicle


class ClaimIntakeError(ValueError):
    pass


class ClaimIntakeService:
    def __init__(
        self,
        settings: Settings,
        claims: MongoClaimRepository,
        jobs: MongoJobQueue,
        blobs: LocalBlobStore,
    ) -> None:
        self._settings = settings
        self._claims = claims
        self._jobs = jobs
        self._blobs = blobs

    def submit(
        self,
        user: CurrentUser,
        body: ClaimCreateRequest,
        *,
        uploads: list[tuple[str, bytes]],
    ) -> PersistedClaim:
        if not user.org_id:
            raise ClaimIntakeError("User is not assigned to an organization")

        self._validate_upload_batch(uploads)

        claim_id = self._claims.next_claim_id()
        now = datetime.now(timezone.utc)
        vin = body.vin
        mileage: int | None = None
        if body.mileage is not None:
            raw = str(body.mileage).strip()
            if raw.isdigit():
                mileage = int(raw)
        engine_type = (body.engine_type or "").strip() or None
        vehicle = Vehicle(
            vehicle_id=f"VIN-{vin}" if vin else f"VEH-{claim_id}",
            vin=vin,
            make=body.make.strip(),
            model=body.model.strip(),
            model_year=int(body.year),
            mileage=mileage,
            engine_type=engine_type,
        )
        repair = Repair(
            repair_category=body.category,
            part_description=body.recommended_repair.strip()[:500],
            recommended_action=body.recommended_repair.strip(),
        )
        claim = ClaimInput(
            claim_id=claim_id,
            submission_date=now,
            vehicle=vehicle,
            customer_complaint=body.customer_complaint.strip(),
            technician_diagnosis=body.technician_diagnosis.strip(),
            recommended_repair=repair,
            submitted_parts_cost=body.parts_cost_decimal(),
            submitted_labour_hours=body.labour_hours_decimal(),
            currency=body.currency,
            claim_status=ClaimStatus.SUBMITTED,
        )

        pending: list[dict[str, Any]] = []
        for name, content in uploads:
            validated = validate_upload(name, content, max_file_bytes=self._settings.CLAIMS_MAX_FILE_BYTES)
            meta = self._blobs.save(claim_id, content, suffix=f".{validated.detected_kind}")
            pending.append(
                {
                    "upload_id": str(uuid4()),
                    "original_filename": validated.original_filename,
                    "detected_kind": validated.detected_kind,
                    **meta,
                }
            )

        job_id = str(uuid4())
        idempotency_key = f"{JobType.CLAIM_INVESTIGATION.value}:{claim_id}:v1"
        record = PersistedClaim(
            org_id=user.org_id,
            claim=claim,
            metadata=ClaimMetadata(
                repair_order=body.repair_order.strip(),
                submitted_by_user_id=user.user_id,
                submitted_by_email=user.email,
            ),
            processing_status=initial_processing_status(len(pending)),
            pending_uploads=pending,
            outbox=[
                ClaimOutboxEvent(
                    event="ENQUEUE_INVESTIGATION",
                    job_id=job_id,
                    processed=False,
                )
            ],
            created_at=now,
            updated_at=now,
        )

        self._persist_with_job(record, job_id=job_id, idempotency_key=idempotency_key)
        return record

    def _persist_with_job(self, record: PersistedClaim, *, job_id: str, idempotency_key: str) -> None:
        from app.auth.mongodb import get_mongo_client

        client = get_mongo_client()
        try:
            with client.start_session() as session:
                with session.start_transaction():
                    self._claims.insert(record, session=session)
                    job = self._jobs.enqueue(
                        claim_id=record.claim_id,
                        org_id=record.org_id,
                        idempotency_key=idempotency_key,
                        max_attempts=self._settings.JOB_MAX_ATTEMPTS,
                        job_id=job_id,
                        session=session,
                    )
                    self._claims.mark_outbox_processed(record.claim_id, record.org_id, job.job_id)
            return
        except OperationFailure:
            pass

        self._claims.insert(record)
        job = self._jobs.enqueue(
            claim_id=record.claim_id,
            org_id=record.org_id,
            idempotency_key=idempotency_key,
            max_attempts=self._settings.JOB_MAX_ATTEMPTS,
            job_id=job_id,
        )
        self._claims.mark_outbox_processed(record.claim_id, record.org_id, job.job_id)

    def _validate_upload_batch(self, uploads: list[tuple[str, bytes]]) -> None:
        if len(uploads) > self._settings.CLAIMS_MAX_FILES:
            raise ClaimIntakeError(f"At most {self._settings.CLAIMS_MAX_FILES} files allowed")
        total = sum(len(b) for _, b in uploads)
        if total > self._settings.CLAIMS_MAX_TOTAL_UPLOAD_BYTES:
            raise ClaimIntakeError("Total upload size exceeds limit")

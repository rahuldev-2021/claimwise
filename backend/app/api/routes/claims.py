from enum import Enum
from typing import Annotated, Optional

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from app.api.deps.claims import get_blob_store, get_claim_service, get_intake_service
from app.api.schemas.claim_create import ClaimCreateRequest
from app.auth.dependencies import CurrentUser, require_permissions
from app.auth.org_access import can_access_org, is_super_admin
from app.modules.claim_documents.blob_store import LocalBlobStore
from app.core.exceptions import ClaimNotFoundError
from app.repositories.mongo_claim_repository import MongoClaimRepository
from app.auth.mongodb import get_auth_db
from app.core.config import get_settings
from app.schemas.claim import ClaimInput, ClaimStatus
from app.schemas.processing_status import ProcessingStatus
from app.services.claim_intake_service import ClaimIntakeError, ClaimIntakeService
from app.services.claim_service import ClaimService

router = APIRouter(tags=["claims"])


class ClaimSort(str, Enum):
    SUBMISSION_DATE_DESC = "submission_date_desc"
    SUBMISSION_DATE_ASC = "submission_date_asc"


@router.get("/claims", response_model=list[ClaimInput])
def list_claims(
    user: Annotated[CurrentUser, Depends(require_permissions("claims:read"))],
    claim_service: Annotated[ClaimService, Depends(get_claim_service)],
    q: Optional[str] = Query(default=None, description="Claim ID substring"),
    status: Optional[ClaimStatus] = None,
    repair_category: Optional[str] = None,
    sort: ClaimSort = ClaimSort.SUBMISSION_DATE_DESC,
) -> list[ClaimInput]:
    claims = claim_service.list_claims_for_user(user)
    if q and q.strip():
        needle = q.strip().lower()
        claims = [c for c in claims if needle in c.claim_id.lower()]
    if status:
        claims = [c for c in claims if c.claim_status == status]
    if repair_category and repair_category.strip():
        category = repair_category.strip().upper()
        claims = [c for c in claims if c.recommended_repair.repair_category == category]
    return sorted(
        claims,
        key=lambda c: c.submission_date,
        reverse=sort == ClaimSort.SUBMISSION_DATE_DESC,
    )


@router.get("/claims/{claim_id}", response_model=ClaimInput)
def get_claim(
    claim_id: str,
    user: Annotated[CurrentUser, Depends(require_permissions("claims:read"))],
    claim_service: Annotated[ClaimService, Depends(get_claim_service)],
) -> ClaimInput:
    try:
        return claim_service.get_claim_for_user(claim_id, user)
    except ClaimNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/claims/{claim_id}/processing-status", response_model=ProcessingStatus)
def get_processing_status(
    claim_id: str,
    user: Annotated[CurrentUser, Depends(require_permissions("claims:read"))],
    claim_service: Annotated[ClaimService, Depends(get_claim_service)],
) -> ProcessingStatus:
    try:
        return claim_service.get_processing_status(claim_id, user)
    except ClaimNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _submit_claim(
    user: CurrentUser,
    intake: ClaimIntakeService,
    body: ClaimCreateRequest,
    uploads: list[tuple[str, bytes]],
) -> ClaimInput:
    try:
        record = intake.submit(user, body, uploads=uploads)
    except ClaimIntakeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return record.claim


@router.post("/claims/json", response_model=ClaimInput, status_code=status.HTTP_201_CREATED)
def create_claim_json(
    user: Annotated[CurrentUser, Depends(require_permissions("claims:submit"))],
    intake: Annotated[ClaimIntakeService, Depends(get_intake_service)],
    body: Annotated[ClaimCreateRequest, Body()],
) -> ClaimInput:
    """Raw JSON body (Postman / curl). Use this when not sending multipart."""
    return _submit_claim(user, intake, body, [])


@router.post("/claims", response_model=ClaimInput, status_code=status.HTTP_201_CREATED)
async def create_claim(
    user: Annotated[CurrentUser, Depends(require_permissions("claims:submit"))],
    intake: Annotated[ClaimIntakeService, Depends(get_intake_service)],
    payload: Annotated[str, Form(description="JSON string matching ClaimCreateRequest")],
    files: Annotated[list[UploadFile], File()] = [],
) -> ClaimInput:
    """Multipart submit (CLAIMWISE UI): form field `payload` + optional `files`."""
    try:
        body = ClaimCreateRequest.model_validate_json(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    uploads: list[tuple[str, bytes]] = []
    for f in files:
        if not f.filename:
            continue
        uploads.append((f.filename, await f.read()))

    return _submit_claim(user, intake, body, uploads)


@router.get("/claims/{claim_id}/documents/{document_id}")
def download_claim_document(
    claim_id: str,
    document_id: str,
    user: Annotated[CurrentUser, Depends(require_permissions("claims:read"))],
    blobs: Annotated[LocalBlobStore, Depends(get_blob_store)],
):
    settings = get_settings()
    db = get_auth_db(settings)
    repo = MongoClaimRepository(db)
    org_filter = None if is_super_admin(user) else user.org_id
    record = repo.get_by_claim_id(claim_id, org_id=org_filter)
    if not record or not can_access_org(user, record.org_id):
        raise HTTPException(status_code=404, detail="Claim not found")
    storage_ref = (record.file_index or {}).get(document_id)
    if not storage_ref:
        raise HTTPException(status_code=404, detail="Document not found")
    try:
        content = blobs.read(storage_ref)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return StreamingResponse(iter([content]), media_type="application/octet-stream")

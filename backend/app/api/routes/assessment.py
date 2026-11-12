from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps.claims import get_claim_service
from app.api.schemas.assessment_requests import AssessmentAnalyzeRequest
from app.auth.dependencies import CurrentUser, require_permissions
from app.core.config import get_settings
from app.core.exceptions import ClaimNotFoundError
from app.services.claim_service import ClaimService
from app.schemas.claim_assessment import ClaimAssessmentResponse
from app.services.assessment_service import AssessmentService
from app.services.rag_service import RAGNotReadyError

router = APIRouter(tags=["assessment"])
_settings = get_settings()
_assessment_service = AssessmentService(_settings)


@router.get("/claims/{claim_id}/assessment/latest", response_model=ClaimAssessmentResponse)
def get_latest_claim_assessment(
    claim_id: str,
    user: Annotated[CurrentUser, Depends(require_permissions("claims:read"))],
    claim_service: Annotated[ClaimService, Depends(get_claim_service)],
) -> ClaimAssessmentResponse:
    claim_service.get_claim_for_user(claim_id.strip(), user)
    snapshot = _assessment_service.get_latest_for_user(claim_id.strip(), user)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="No assessment snapshot for this claim")
    return snapshot


@router.post("/assessment/analyze", response_model=ClaimAssessmentResponse)
def analyze_claim_assessment(
    request: AssessmentAnalyzeRequest,
    user: Annotated[CurrentUser, Depends(require_permissions("claims:assess"))],
    claim_service: Annotated[ClaimService, Depends(get_claim_service)],
) -> ClaimAssessmentResponse:
    try:
        if request.claim_id:
            claim_service.get_claim_for_user(request.claim_id.strip(), user)
            return _assessment_service.analyze_by_claim_id_for_user(
                request.claim_id.strip(),
                user,
                top_k=request.top_k,
                retrieval_mode=request.retrieval_mode,
                auto_ingest=request.auto_ingest,
                llm_enabled=request.llm_enabled,
                financial_enabled=request.financial_enabled,
                force_refresh=request.force_refresh,
            )
        assert request.claim is not None
        return _assessment_service.analyze_claim_for_user(
            request.claim,
            user,
            top_k=request.top_k,
            retrieval_mode=request.retrieval_mode,
            auto_ingest=request.auto_ingest,
            llm_enabled=request.llm_enabled,
            financial_enabled=request.financial_enabled,
            force_refresh=request.force_refresh,
        )
    except ClaimNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RAGNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

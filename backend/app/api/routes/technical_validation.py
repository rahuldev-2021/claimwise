from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps.claims import get_claim_service
from app.api.schemas.technical_validation_requests import TechnicalValidationAnalyzeRequest
from app.auth.dependencies import CurrentUser, require_permissions
from app.core.config import get_settings
from app.core.exceptions import ClaimNotFoundError
from app.schemas.technical_validation import TechnicalValidationResult
from app.services.claim_service import ClaimService
from app.services.rag_service import RAGNotReadyError
from app.services.technical_validation_service import TechnicalValidationService

router = APIRouter(tags=["technical-validation"])
_settings = get_settings()
_tv_service = TechnicalValidationService(_settings)


@router.post("/technical-validation/analyze", response_model=TechnicalValidationResult)
def analyze_technical_validation(
    request: TechnicalValidationAnalyzeRequest,
    user: Annotated[CurrentUser, Depends(require_permissions("claims:assess"))],
    claim_service: Annotated[ClaimService, Depends(get_claim_service)],
) -> TechnicalValidationResult:
    try:
        if request.claim_id:
            claim_service.get_claim_for_user(request.claim_id.strip(), user)
            return _tv_service.analyze_by_claim_id_for_user(
                request.claim_id.strip(),
                user,
                top_k=request.top_k,
                retrieval_mode=request.retrieval_mode,
                auto_ingest=request.auto_ingest,
            )
        assert request.claim is not None
        return _tv_service.analyze_claim_for_user(
            request.claim,
            user,
            top_k=request.top_k,
            retrieval_mode=request.retrieval_mode,
            auto_ingest=request.auto_ingest,
        )
    except ClaimNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RAGNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

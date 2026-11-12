from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps.claims import get_claim_service
from app.api.schemas.recommendation_requests import RecommendationAnalyzeRequest
from app.auth.dependencies import CurrentUser, require_permissions
from app.core.config import get_settings
from app.core.exceptions import ClaimNotFoundError
from app.schemas.recommendation_analyze import RecommendationAnalyzeResponse
from app.services.claim_service import ClaimService
from app.services.rag_service import RAGNotReadyError
from app.services.recommendation_service import RecommendationService

router = APIRouter(tags=["recommendations"])
_settings = get_settings()
_recommendation_service = RecommendationService(_settings)


@router.post("/recommendations/analyze", response_model=RecommendationAnalyzeResponse)
def analyze_recommendations(
    request: RecommendationAnalyzeRequest,
    user: Annotated[CurrentUser, Depends(require_permissions("claims:assess"))],
    claim_service: Annotated[ClaimService, Depends(get_claim_service)],
) -> RecommendationAnalyzeResponse:
    try:
        claim_service.get_claim_for_user(request.claim_id.strip(), user)
        return _recommendation_service.analyze_for_user(
            request.claim_id,
            user,
            force_refresh=request.force_refresh,
            llm_enabled=request.llm_enabled,
            llm_provider=request.llm_provider,
            top_k=request.top_k,
            auto_ingest=request.auto_ingest,
        )
    except ClaimNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RAGNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

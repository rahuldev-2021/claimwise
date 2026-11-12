from fastapi import APIRouter, HTTPException

from app.api.schemas.nlp_requests import NLPAnalyzeRequest
from app.core.config import get_settings
from app.core.exceptions import ClaimNotFoundError
from app.modules.nlp.schemas import NLPAnalysisResult
from app.services.nlp_analysis_service import NLPAnalysisService

router = APIRouter(tags=["nlp"])

_settings = get_settings()
_nlp_service = NLPAnalysisService(_settings)


@router.post("/nlp/analyze", response_model=NLPAnalysisResult)
def analyze_claim(request: NLPAnalyzeRequest) -> NLPAnalysisResult:
    try:
        if request.claim_id:
            return _nlp_service.analyze_by_claim_id(request.claim_id.strip())
        assert request.claim is not None
        return _nlp_service.analyze_claim(request.claim)
    except ClaimNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

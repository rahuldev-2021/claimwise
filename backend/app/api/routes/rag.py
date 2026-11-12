import logging

from fastapi import APIRouter, HTTPException

from app.api.schemas.rag_requests import (
    RAGIngestRequest,
    RAGRetrieveForClaimRequest,
    RAGSearchRequest,
)
from app.core.config import get_settings
from app.core.exceptions import ClaimNotFoundError
from app.modules.rag.embedding_provider import EmbeddingError
from app.modules.rag.schemas import EvaluationReport, IngestReport, RAGHealthStatus, RetrievalResult
from app.modules.rag.vector_store import VectorStoreError
from app.auth.mongodb import get_auth_db
from app.modules.rag.historical_repair_adapter import persist_historical_rows_to_mongo
from app.services.rag_service import RAGNotReadyError
from app.services.rag_service_provider import get_rag_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["rag"])
_settings = get_settings()


def _rag_service():
    return get_rag_service(_settings)


@router.get("/rag/health", response_model=RAGHealthStatus)
def rag_health() -> RAGHealthStatus:
    return _rag_service().health()


@router.post("/rag/ingest", response_model=IngestReport)
def rag_ingest(request: RAGIngestRequest) -> IngestReport:
    try:
        persist_historical_rows_to_mongo(get_auth_db(), _settings)
        return _rag_service().ingest(
            force_reindex=request.force_reindex,
            document_ids=request.document_ids,
        )
    except (EmbeddingError, VectorStoreError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/rag/search", response_model=RetrievalResult)
def rag_search(request: RAGSearchRequest) -> RetrievalResult:
    try:
        return _rag_service().search(
            request.query,
            top_k=request.top_k,
            mode=request.mode,
            metadata_filters=request.metadata_filters or None,
            expand=request.expand,
            rerank=request.rerank,
        )
    except RAGNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (EmbeddingError, VectorStoreError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/rag/retrieve-for-claim", response_model=RetrievalResult)
def rag_retrieve_for_claim(request: RAGRetrieveForClaimRequest) -> RetrievalResult:
    try:
        filter_fields = tuple(request.filter_fields) if request.filter_fields else ("repair_category",)
        if request.claim_id:
            return _rag_service().retrieve_for_claim_id(
                request.claim_id.strip(),
                top_k=request.top_k,
                mode=request.mode,
                filter_fields=filter_fields,
                expand=request.expand,
                rerank=request.rerank,
            )
        assert request.claim is not None
        return _rag_service().retrieve_for_claim(
            request.claim,
            top_k=request.top_k,
            mode=request.mode,
            filter_fields=filter_fields,
            expand=request.expand,
            rerank=request.rerank,
        )
    except ClaimNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RAGNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (EmbeddingError, VectorStoreError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/rag/evaluate", response_model=EvaluationReport)
def rag_evaluate(k: int = 5) -> EvaluationReport:
    try:
        return _rag_service().run_evaluation(k=k)
    except RAGNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

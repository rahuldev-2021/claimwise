"""Orchestrates document ingestion, retrieval, and evaluation."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Optional

from app.core.config import Settings
from app.core.exceptions import ClaimNotFoundError, DocumentNotFoundError
from app.modules.nlp.schemas import NLPAnalysisResult
from app.modules.rag.chunking import ChunkingConfig, RecursiveChunker
from app.modules.rag.document_cleaner import is_blank
from app.modules.rag.document_loader import DocumentLoader
from app.modules.rag.embedding_provider import (
    DeterministicEmbeddingProvider,
    EmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
)
from app.modules.rag.evaluation import EvaluationHarness
from app.modules.rag.ingestion import IngestionPipeline
from app.modules.rag.lexical_retriever import BM25Retriever
from app.modules.rag.metadata_filter import build_where
from app.modules.rag.retrieval_access import RetrievalAccessContext
from app.modules.rag.retrieval_pipeline import RetrievalPipeline
from app.modules.rag.runtime import ParentTextRegistry, create_chroma_client
from app.modules.rag.schemas import (
    EvaluationReport,
    IngestReport,
    RAGHealthStatus,
    RetrievalMode,
    RetrievalResult,
)
from app.modules.rag.vector_store import ChromaVectorStore, VectorStoreError
from app.modules.rag.citation_manager import CitationManager
from app.schemas.claim import ClaimInput
from app.schemas.repair_document import RepairDocument
from app.services.claim_service import ClaimService
from app.services.nlp_analysis_service import NLPAnalysisService

logger = logging.getLogger(__name__)


class RAGNotReadyError(Exception):
    """Raised when the vector index is empty or the store is unavailable."""


class RAGService:
    def __init__(
        self,
        settings: Settings,
        *,
        embedding_provider: EmbeddingProvider | None = None,
        chroma_client: object | None = None,
        persist: bool | None = None,
    ) -> None:
        self._settings = settings
        self._claims = ClaimService(settings)
        self._nlp = NLPAnalysisService(settings)
        self._parent_registry = ParentTextRegistry()
        parent_map = self._parent_registry.mapping

        if embedding_provider is None:
            embedding_provider = SentenceTransformerEmbeddingProvider(
                model_name=settings.RAG_EMBEDDING_MODEL
            )
        self._embeddings = embedding_provider

        use_persist = persist if persist is not None else settings.APP_ENV != "test"
        collection_name = settings.RAG_COLLECTION_NAME
        if not use_persist:
            collection_name = f"{settings.RAG_COLLECTION_NAME}_test_{uuid.uuid4().hex[:8]}"
        if chroma_client is None:
            chroma_client = create_chroma_client(
                persist_dir=settings.RAG_PERSIST_DIR if use_persist else None
            )
        self._store = ChromaVectorStore(
            chroma_client,
            collection_name=collection_name,
            embedding_dimension=self._embeddings.dimension,
        )
        self._lexical = BM25Retriever()
        chunker = RecursiveChunker(
            ChunkingConfig(
                chunk_size=settings.RAG_CHUNK_SIZE,
                chunk_overlap=settings.RAG_CHUNK_OVERLAP,
            )
        )

        def document_lookup(document_id: str) -> RepairDocument | None:
            try:
                return self._claims.get_document(document_id)
            except DocumentNotFoundError:
                return None

        citation_manager = CitationManager(document_lookup=document_lookup)
        self._ingestion = IngestionPipeline(
            embeddings=self._embeddings,
            store=self._store,
            lexical=self._lexical,
            chunker=chunker,
            parent_map=parent_map,
        )
        default_mode = (
            RetrievalMode.BASIC
            if settings.RAG_DEFAULT_MODE.lower() == "basic"
            else RetrievalMode.ADVANCED
        )
        self._default_mode = default_mode
        self._retrieval = RetrievalPipeline(
            embeddings=self._embeddings,
            store=self._store,
            lexical=self._lexical,
            citation_manager=citation_manager,
            parent_map=parent_map,
            rrf_k=settings.RAG_RRF_K,
            retrieval_depth=settings.RAG_RETRIEVAL_DEPTH,
            relevance_threshold=settings.RAG_RELEVANCE_THRESHOLD,
            scope_fetch_multiplier=settings.RAG_SCOPE_FETCH_MULTIPLIER,
        )
        self._loader = DocumentLoader()
        self._evaluator = EvaluationHarness(self._retrieval, self._lexical)

    @classmethod
    def for_tests(cls, settings: Settings) -> "RAGService":
        """Construct a service with ephemeral storage and deterministic embeddings."""
        test_settings = settings.model_copy(update={"APP_ENV": "test"})
        return cls(
            test_settings,
            embedding_provider=DeterministicEmbeddingProvider(),
            persist=False,
        )

    def ingest(
        self,
        *,
        force_reindex: bool = False,
        document_ids: Optional[list[str]] = None,
        include_historical: bool | None = None,
    ) -> IngestReport:
        documents = self._loader.from_repository(self._claims)
        use_historical = (
            include_historical
            if include_historical is not None
            else self._settings.HISTORICAL_REPAIRS_INGEST_ENABLED
        )
        if use_historical:
            from app.modules.rag.historical_repair_adapter import load_historical_as_documents

            documents = documents + load_historical_as_documents(self._settings)
        if document_ids:
            wanted = {d.strip() for d in document_ids if d and d.strip()}
            documents = [d for d in documents if d.document_id in wanted]
        prepared: list[RepairDocument] = []
        for doc in documents:
            prepared.append(
                doc.model_copy(
                    update={
                        "evidence_scope": "global",
                        "claim_id": None,
                        "synthetic": doc.synthetic or True,
                    }
                )
            )
        return self.ingest_documents(prepared, force_reindex=force_reindex)

    def ingest_documents(
        self,
        documents: list[RepairDocument],
        *,
        force_reindex: bool = False,
    ) -> IngestReport:
        report = self._ingestion.ingest(documents, force_reindex=force_reindex)
        self._parent_registry.merge(self._ingestion.parent_map)
        return report

    def purge_document_from_index(self, document_id: str) -> bool:
        """Drop searchable chunks for a document; Mongo remains authoritative."""
        purged = self._ingestion.purge_document(document_id)
        if purged:
            self._parent_registry.merge({})
        return purged

    def has_document_in_index(self, document_id: str) -> bool:
        try:
            return self._store.has_document(document_id)
        except VectorStoreError:
            return False

    def rebuild_lexical_index(self) -> int:
        """Rebuild in-memory BM25 from the persisted vector store."""
        self._ingestion.rebuild_lexical_from_store()
        return len(self._lexical)

    def indexed_document_ids(self) -> set[str]:
        ids: set[str] = set()
        try:
            for item in self._store.list_all():
                meta = item.get("metadata") or {}
                doc_id = str(meta.get("document_id", ""))
                if doc_id:
                    ids.add(doc_id)
        except VectorStoreError:
            pass
        return ids

    def _corpus_document_ids(self, *, include_historical: bool | None = None) -> set[str]:
        documents = self._loader.from_repository(self._claims)
        use_historical = (
            include_historical
            if include_historical is not None
            else self._settings.HISTORICAL_REPAIRS_INGEST_ENABLED
        )
        if use_historical:
            from app.modules.rag.historical_repair_adapter import load_historical_as_documents

            documents = documents + load_historical_as_documents(self._settings)
        return {d.document_id for d in documents if not is_blank(d.content)}

    def ensure_startup_corpus(self) -> IngestReport | None:
        """Idempotent startup: index missing corpus docs; rebuild BM25 when Chroma is warm."""
        try:
            chunk_count = self._store.count()
        except VectorStoreError as exc:
            logger.warning("RAG startup ingest skipped: %s", exc)
            return None

        corpus_ids = self._corpus_document_ids()
        indexed_ids = self.indexed_document_ids() if chunk_count > 0 else set()
        missing = corpus_ids - indexed_ids
        lexical_needed = chunk_count > 0 and not self._lexical.is_built

        if not missing and chunk_count > 0 and not lexical_needed:
            logger.info(
                "RAG startup: corpus up to date (%d chunks, %d indexed documents)",
                chunk_count,
                len(indexed_ids),
            )
            return None

        if missing or chunk_count == 0:
            logger.info(
                "RAG startup: incremental ingest (%d missing of %d corpus documents, %d chunks now)",
                len(missing),
                len(corpus_ids),
                chunk_count,
            )
            return self.ingest(force_reindex=False)

        if lexical_needed:
            logger.info("RAG startup: rebuilding BM25 from %d persisted chunks", chunk_count)
            self.rebuild_lexical_index()
        return None

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        mode: RetrievalMode | None = None,
        metadata_filters: dict[str, object] | None = None,
        expand: bool = True,
        rerank: bool = False,
    ) -> RetrievalResult:
        self._ensure_indexed()
        where = build_where(metadata_filters)
        return self._retrieval.retrieve(
            query,
            top_k=top_k,
            mode=mode or self._default_mode,
            where=where,
            expand=expand,
            rerank=rerank,
        )

    def retrieve_for_claim_id(self, claim_id: str, **kwargs) -> RetrievalResult:
        claim = self._claims.get_claim(claim_id)
        return self.retrieve_for_claim(claim, **kwargs)

    def retrieve_for_claim(
        self,
        claim: ClaimInput,
        *,
        top_k: int = 5,
        mode: RetrievalMode | None = None,
        filter_fields: tuple[str, ...] = ("repair_category",),
        expand: bool = True,
        rerank: bool = False,
        run_nlp: bool = True,
        nlp_result: NLPAnalysisResult | None = None,
        access: RetrievalAccessContext | None = None,
    ) -> RetrievalResult:
        self._ensure_indexed()
        if run_nlp:
            nlp_result = self._nlp.analyze_claim(claim)
        hard_fields = tuple(
            f.strip()
            for f in self._settings.RAG_CLAIM_HARD_FILTER_FIELDS.split(",")
            if f.strip()
        ) or filter_fields
        return self._retrieval.retrieve_for_claim(
            claim,
            nlp_result,
            top_k=top_k,
            mode=mode or self._default_mode,
            filter_fields=hard_fields,
            expand=expand,
            rerank=rerank,
            min_passages_fallback=self._settings.RAG_MIN_PASSAGES_FALLBACK,
            fallback_filter_fields=("repair_category",),
            access=access,
        )

    def health(self) -> RAGHealthStatus:
        count = 0
        document_ids: set[str] = set()
        try:
            count = self._store.count()
            for item in self._store.list_all():
                meta = item.get("metadata") or {}
                doc_id = str(meta.get("document_id", ""))
                if doc_id:
                    document_ids.add(doc_id)
        except VectorStoreError as exc:
            logger.warning("RAG health store check failed: %s", exc)
        return RAGHealthStatus(
            indexed=count > 0,
            chunk_count=count,
            document_count=len(document_ids),
            embedding_model=self._embeddings.model_name,
            embedding_dimension=self._embeddings.dimension,
            persist_dir=self._settings.RAG_PERSIST_DIR,
            collection_name=self._settings.RAG_COLLECTION_NAME,
        )

    def run_evaluation(
        self,
        *,
        dataset_path: str | Path | None = None,
        k: int = 5,
    ) -> EvaluationReport:
        self._ensure_indexed()
        path = (
            Path(dataset_path)
            if dataset_path
            else Path(self._settings.SAMPLE_DATA_DIR).parent / "rag" / "evaluation_queries.json"
        )
        indexed_chunks = {
            str(item.get("chunk_id", ""))
            for item in self._store.list_all()
            if item.get("chunk_id")
        }
        missing = self._evaluator.validate_labelled_chunks(path, indexed_chunks)
        if missing:
            logger.warning(
                "Evaluation labels reference unknown chunk IDs: %s",
                ", ".join(missing[:10]),
            )
        return self._evaluator.run(path, k=k)

    def _ensure_indexed(self) -> None:
        try:
            count = self._store.count()
            if count <= 0:
                raise RAGNotReadyError(
                    "Vector index is empty. Run POST /api/v1/rag/ingest first."
                )
            if not self._lexical.is_built:
                logger.info("Rebuilding BM25 lexical index from %d persisted chunks", count)
                self.rebuild_lexical_index()
        except VectorStoreError as exc:
            raise RAGNotReadyError(f"Vector store unavailable: {exc}") from exc

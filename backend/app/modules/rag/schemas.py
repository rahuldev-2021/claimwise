"""Pydantic models for the Phase 3 RAG retrieval pipeline.

These schemas formalize the retrieval output contract that was a placeholder
(``RetrievalResult``) in ``app/services/interfaces.py``.  They are consumed by
the later technical-validation module (Phase 4) and by the API layer.

Design notes
------------
* Every retrieved passage carries full source traceability (document id,
  chunk id, title, document type, verification status) so a downstream
  reviewer can trace any passage back to its origin.  Citations are never
  fabricated.
* ``RetrievalResult`` is the single structured response returned by the
  retrieval pipeline regardless of which strategy (semantic / lexical /
  hybrid) produced it.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field


class RetrievalStrategy(str, Enum):
    """Which retrieval path produced a result set."""

    SEMANTIC = "semantic"
    LEXICAL = "lexical"
    HYBRID = "hybrid"


class RetrievalMode(str, Enum):
    """Configurable pipeline mode.  ``basic`` = semantic only,
    ``advanced`` = hybrid (semantic + lexical + RRF) with optional rerank."""

    BASIC = "basic"
    ADVANCED = "advanced"


class IngestStatus(str, Enum):
    """Per-document outcome of an ingestion run."""

    INDEXED = "INDEXED"
    SKIPPED_DUPLICATE = "SKIPPED_DUPLICATE"
    SKIPPED_EMPTY = "SKIPPED_EMPTY"
    ERROR = "ERROR"


class IngestedDocumentRecord(BaseModel):
    """Outcome for a single document during ingestion."""

    model_config = ConfigDict(extra="forbid")

    document_id: str
    status: IngestStatus
    chunk_count: int = 0
    error: Optional[str] = None


class IngestReport(BaseModel):
    """Aggregate result of an ingestion run."""

    model_config = ConfigDict(extra="forbid")

    total_documents: int = 0
    indexed: int = 0
    skipped_duplicate: int = 0
    skipped_empty: int = 0
    errors: int = 0
    total_chunks: int = 0
    embedding_model: str = ""
    embedding_dimension: int = 0
    records: list[IngestedDocumentRecord] = Field(default_factory=list)


class Chunk(BaseModel):
    """A single indexed text chunk with its source metadata.

    ``parent_text`` is populated only for documents long enough to benefit
    from parent-child retrieval; it carries the surrounding section so a
    retrieved child chunk can be understood in context.
    """

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    document_id: str
    text: str
    metadata: dict[str, object] = Field(default_factory=dict)
    parent_text: Optional[str] = None


class VectorHit(BaseModel):
    """A single result from semantic (vector) retrieval."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    document_id: str
    text: str
    score: float
    rank: int
    metadata: dict[str, object] = Field(default_factory=dict)


class LexicalHit(BaseModel):
    """A single result from BM25 lexical retrieval."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    document_id: str
    text: str
    score: float
    rank: int
    metadata: dict[str, object] = Field(default_factory=dict)


class HybridHit(BaseModel):
    """A fused result from hybrid (RRF) retrieval.

    ``semantic_score`` / ``lexical_score`` are the original per-method scores
    (``None`` when the chunk was not returned by that method).  ``rrf_score``
    is the fusion score used for final ranking.
    """

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    document_id: str
    text: str
    rrf_score: float
    rank: int
    semantic_score: Optional[float] = None
    lexical_score: Optional[float] = None
    metadata: dict[str, object] = Field(default_factory=dict)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def score(self) -> float:
        """Unified score for citation assembly (equals RRF fusion score)."""
        return self.rrf_score


class RAGHealthStatus(BaseModel):
    """Index and runtime status for RAG health checks."""

    model_config = ConfigDict(extra="forbid")

    indexed: bool
    chunk_count: int = 0
    document_count: int = 0
    embedding_model: str = ""
    embedding_dimension: int = 0
    persist_dir: str = ""
    collection_name: str = ""


class EvaluationCaseResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_id: str
    query: str
    precision_at_k: float = 0.0
    recall_at_k: float = 0.0
    reciprocal_rank: float = 0.0
    ndcg_at_k: float = 0.0
    hit: bool = False
    retrieved_document_ids: list[str] = Field(default_factory=list)


class StrategyEvaluationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy: str
    k: int
    mean_precision_at_k: float = 0.0
    mean_recall_at_k: float = 0.0
    mrr: float = 0.0
    mean_ndcg_at_k: float = 0.0
    hit_rate_at_k: float = 0.0
    case_results: list[EvaluationCaseResult] = Field(default_factory=list)


class EvaluationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_path: str
    dataset_size: int
    k: int
    summaries: list[StrategyEvaluationSummary] = Field(default_factory=list)
    limitation_note: str = (
        "Evaluation uses a small labelled set on the synthetic corpus; "
        "metrics are illustrative, not production benchmarks."
    )


class RetrievedPassage(BaseModel):
    """A single passage in the final retrieval response, fully cited."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    document_id: str
    title: str
    document_type: str
    verification_status: str
    evidence_scope: str = ""
    evidence_source_type: str = ""
    text: str
    parent_text: Optional[str] = None
    retrieval_method: RetrievalStrategy
    score: float
    rank: int
    rerank_score: Optional[float] = None
    metadata: dict[str, object] = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    """Structured retrieval response.

    This is the formal contract that ``RAGModule.retrieve`` returns and that
    the Phase 4 technical-validation module consumes.  It is evidence only —
    it does not assert that any repair is technically correct.
    """

    model_config = ConfigDict(extra="forbid")

    query: str
    strategy: RetrievalStrategy
    passages: list[RetrievedPassage] = Field(default_factory=list)
    source_document_ids: list[str] = Field(default_factory=list)
    total_candidates: int = 0
    embedding_model: str = ""
    embedding_dimension: int = 0
    filter_fallback_applied: bool = False
    note: str = ()

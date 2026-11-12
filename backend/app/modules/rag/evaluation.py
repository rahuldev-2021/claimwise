"""Labelled retrieval evaluation (Precision@K, Recall@K, MRR, nDCG@K)."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from app.modules.rag.lexical_retriever import BM25Retriever
from app.modules.rag.retrieval_pipeline import RetrievalPipeline
from app.modules.rag.schemas import (
    EvaluationCaseResult,
    EvaluationReport,
    RetrievalMode,
    StrategyEvaluationSummary,
)


@dataclass(frozen=True)
class LabelledQuery:
    query_id: str
    query: str
    relevant_document_ids: frozenset[str]
    relevant_chunk_ids: frozenset[str] = frozenset()


class EvaluationHarness:
    def __init__(self, pipeline: RetrievalPipeline, lexical: BM25Retriever) -> None:
        self._pipeline = pipeline
        self._lexical = lexical

    def load_dataset(self, path: Path) -> list[LabelledQuery]:
        raw = json.loads(path.read_text(encoding="utf-8"))
        cases: list[LabelledQuery] = []
        for item in raw:
            doc_ids = frozenset(item.get("relevant_document_ids") or [])
            chunk_ids = frozenset(item.get("relevant_chunk_ids") or [])
            cases.append(
                LabelledQuery(
                    query_id=item["query_id"],
                    query=item["query"],
                    relevant_document_ids=doc_ids,
                    relevant_chunk_ids=chunk_ids,
                )
            )
        return cases

    def validate_labelled_chunks(self, path: Path, corpus_chunk_ids: set[str]) -> list[str]:
        """Return labels that reference chunk IDs missing from the indexed corpus."""
        missing: list[str] = []
        for case in self.load_dataset(path):
            for cid in case.relevant_chunk_ids:
                if cid not in corpus_chunk_ids:
                    missing.append(f"{case.query_id}:{cid}")
        return missing

    def run(self, path: Path, *, k: int = 5) -> EvaluationReport:
        dataset = self.load_dataset(path)
        strategies = [
            ("semantic", self._retrieve_semantic),
            ("lexical", self._retrieve_lexical),
            ("hybrid", self._retrieve_hybrid),
        ]
        summaries: list[StrategyEvaluationSummary] = []
        for name, retrieve_fn in strategies:
            case_results: list[EvaluationCaseResult] = []
            for case in dataset:
                doc_ids, chunk_ids = retrieve_fn(case.query, k=k)
                metrics = _score_case(case, doc_ids, chunk_ids, k=k)
                case_results.append(
                    EvaluationCaseResult(
                        query_id=case.query_id,
                        query=case.query,
                        precision_at_k=metrics["precision"],
                        recall_at_k=metrics["recall"],
                        reciprocal_rank=metrics["rr"],
                        ndcg_at_k=metrics["ndcg"],
                        hit=metrics["hit"],
                        retrieved_document_ids=doc_ids,
                    )
                )
            summaries.append(
                StrategyEvaluationSummary(
                    strategy=name,
                    k=k,
                    mean_precision_at_k=_mean(r.precision_at_k for r in case_results),
                    mean_recall_at_k=_mean(r.recall_at_k for r in case_results),
                    mrr=_mean(r.reciprocal_rank for r in case_results),
                    mean_ndcg_at_k=_mean(r.ndcg_at_k for r in case_results),
                    hit_rate_at_k=_mean(1.0 if r.hit else 0.0 for r in case_results),
                    case_results=case_results,
                )
            )
        return EvaluationReport(
            dataset_path=str(path),
            dataset_size=len(dataset),
            k=k,
            summaries=summaries,
        )

    def _retrieve_semantic(self, query: str, *, k: int) -> tuple[list[str], list[str]]:
        result = self._pipeline.retrieve(
            query, top_k=k, mode=RetrievalMode.BASIC, expand=False
        )
        return _ids_from_result(result)

    def _retrieve_lexical(self, query: str, *, k: int) -> tuple[list[str], list[str]]:
        hits = self._lexical.retrieve(query, top_k=k)
        doc_ids = []
        chunk_ids = []
        for hit in hits:
            chunk_ids.append(hit.chunk_id)
            if hit.document_id:
                doc_ids.append(hit.document_id)
        return _unique(doc_ids), chunk_ids

    def _retrieve_hybrid(self, query: str, *, k: int) -> tuple[list[str], list[str]]:
        result = self._pipeline.retrieve(
            query, top_k=k, mode=RetrievalMode.ADVANCED, expand=False
        )
        return _ids_from_result(result)


def _ids_from_result(result) -> tuple[list[str], list[str]]:
    doc_ids: list[str] = []
    chunk_ids: list[str] = []
    for passage in result.passages:
        chunk_ids.append(passage.chunk_id)
        if passage.document_id:
            doc_ids.append(passage.document_id)
    return _unique(doc_ids), chunk_ids


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def _score_case(case: LabelledQuery, retrieved_docs: list[str], retrieved_chunks: list[str], *, k: int) -> dict[str, float]:
    relevant_docs = case.relevant_document_ids
    relevant_chunks = case.relevant_chunk_ids

    retrieved_doc_top = retrieved_docs[:k]
    retrieved_chunk_top = retrieved_chunks[:k]

    if relevant_chunks:
        hits = sum(1 for cid in retrieved_chunk_top if cid in relevant_chunks)
        rel_count = len(relevant_chunks) or 1
        relevant_set = relevant_chunks
        ranking_list = retrieved_chunk_top
    else:
        hits = sum(1 for did in retrieved_doc_top if did in relevant_docs)
        rel_count = len(relevant_docs) or 1
        relevant_set = relevant_docs
        ranking_list = retrieved_doc_top

    precision = hits / k if k else 0.0
    recall = hits / rel_count if rel_count else 0.0

    rr = 0.0
    for index, item in enumerate(ranking_list, start=1):
        if item in relevant_set:
            rr = 1.0 / index
            break

    dcg = 0.0
    for index, item in enumerate(ranking_list, start=1):
        if item in relevant_set:
            dcg += 1.0 / math.log2(index + 1)
    ideal_hits = min(len(relevant_set), k)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_hits + 1))
    ndcg = (dcg / idcg) if idcg > 0 else 0.0
    hit = hits > 0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "rr": round(rr, 4),
        "ndcg": round(ndcg, 4),
        "hit": hit,
    }


def _mean(values) -> float:
    items = list(values)
    if not items:
        return 0.0
    return round(sum(items) / len(items), 4)

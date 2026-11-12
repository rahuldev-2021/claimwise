"""CLAIM_INVESTIGATION job: documents → NLP → RAG → technical validation."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.core.config import Settings
from app.jobs.schemas import JobRecord
from app.modules.claim_documents.blob_store import LocalBlobStore
from app.modules.claim_documents.classifier import classify_document_text
from app.modules.claim_documents.text_extractor import extract_text
from app.modules.nlp.pipeline_factory import build_nlp_pipeline
from app.modules.rag.document_cleaner import clean_text
from app.modules.rag.retrieval_access import RetrievalAccessContext
from app.modules.rag.schemas import IngestStatus, RetrievalResult, RetrievalStrategy
from app.modules.rag.upload_index_eligibility import (
    IndexAction,
    assess_claim_upload_for_index,
    content_fingerprint,
)
from app.repositories.mongo_claim_repository import MongoClaimRepository
from app.repositories.mongo_repair_document_repository import MongoRepairDocumentRepository
from app.schemas.claim import ClaimStatus
from app.schemas.processing_status import OverallStatus, ProcessingStatus, StageStatus
from app.schemas.repair_document import RepairDocument, VectorIndexStatus, VerificationStatus
from app.schemas.technical_validation import TechnicalValidationResult
from app.services.rag_service import RAGNotReadyError, RAGService
from app.services.rag_service_provider import get_rag_service
from app.services.technical_validation_service import TechnicalValidationService

logger = logging.getLogger(__name__)


class InvestigationHandler:
    def __init__(
        self,
        settings: Settings,
        claims: MongoClaimRepository,
        documents: MongoRepairDocumentRepository,
        blobs: LocalBlobStore,
    ) -> None:
        self._settings = settings
        self._claims = claims
        self._documents = documents
        self._blobs = blobs
        self._nlp = build_nlp_pipeline(settings)
        use_test_rag = settings.APP_ENV == "test"
        self._rag = RAGService.for_tests(settings) if use_test_rag else get_rag_service(settings)
        self._tv = (
            TechnicalValidationService.for_tests(settings)
            if use_test_rag
            else TechnicalValidationService(settings)
        )

    def run(self, job: JobRecord) -> None:
        record = self._claims.get_by_claim_id(job.claim_id, org_id=job.org_id)
        if not record:
            raise ValueError(f"Claim not found: {job.claim_id}")

        logger.info("Investigation started for claim %s (job %s)", job.claim_id, job.job_id)

        ps = record.processing_status.model_copy(deep=True)
        ps.overall = OverallStatus.PROCESSING

        nlp_result = None
        rag_result: RetrievalResult | None = None
        tv_result: TechnicalValidationResult | None = None

        try:
            doc_ids, file_index = self._process_documents(record, ps)
            ps, nlp_result = self._run_nlp(record, ps)
            if ps.nlp.status == StageStatus.COMPLETED and nlp_result is not None:
                ps, rag_result, tv_result = self._run_rag_and_tv(
                    record, doc_ids, ps, nlp_result
                )
            else:
                ps.rag.status = StageStatus.SKIPPED
                ps.rag.error = "NLP incomplete; retrieval skipped"
                ps.technical_validation.status = StageStatus.SKIPPED
                ps.technical_validation.error = "NLP incomplete"
                ps.touch()

            ps = self._finalize_stages(ps)
            claim_patch: dict = {
                "processing_status": ps.model_dump(mode="json"),
                "claim.supporting_document_ids": doc_ids,
                "pending_uploads": [],
                "file_index": file_index,
            }
            if nlp_result is not None:
                claim_patch["nlp_analysis"] = nlp_result.model_dump(mode="json")
            if rag_result is not None:
                claim_patch["rag_retrieval"] = rag_result.model_dump(mode="json")
            if tv_result is not None:
                claim_patch["technical_validation"] = tv_result.model_dump(mode="json")
            if ps.overall == OverallStatus.READY:
                claim_patch["claim.claim_status"] = ClaimStatus.UNDER_REVIEW.value
            self._claims.update(job.claim_id, job.org_id, claim_patch)
            logger.info(
                "Investigation finished for %s: overall=%s nlp=%s rag=%s tv=%s",
                job.claim_id,
                ps.overall.value,
                ps.nlp.status.value,
                ps.rag.status.value,
                ps.technical_validation.status.value,
            )
        except Exception as exc:
            logger.exception("Investigation failed for %s", job.claim_id)
            ps.overall = OverallStatus.FAILED
            ps.touch()
            self._claims.update(
                job.claim_id,
                job.org_id,
                {
                    "processing_status": ps.model_dump(mode="json"),
                    "claim.claim_status": ClaimStatus.UNDER_REVIEW.value,
                },
            )
            raise exc

    def _process_documents(self, record, ps: ProcessingStatus) -> tuple[list[str], dict[str, str]]:
        uploads = list(record.pending_uploads or [])
        if not uploads:
            ps.documents.status = StageStatus.SKIPPED
            ps.documents.total = 0
            ps.touch()
            return list(record.claim.supporting_document_ids), dict(record.file_index or {})

        ps.documents.status = StageStatus.PROCESSING
        ps.documents.total = len(uploads)
        ps.documents.processed = 0
        ps.documents.failed = 0
        ps.touch()

        doc_ids: list[str] = list(record.claim.supporting_document_ids)
        extracted_snippets: list[str] = []
        file_index = dict(record.file_index or {})

        min_chars = self._settings.RAG_UPLOAD_MIN_TEXT_CHARS
        for upl in uploads:
            try:
                content = self._blobs.read(upl["storage_ref"])
                kind = upl.get("detected_kind", "pdf")
                text = extract_text(kind, content)
                if len(clean_text(text)) < min_chars:
                    ps.documents.failed += 1
                    logger.warning(
                        "Skipping upload %s for %s: insufficient extractable text",
                        upl.get("original_filename"),
                        record.claim_id,
                    )
                    continue
                doc_type = classify_document_text(text, upl.get("original_filename", ""))
                doc_id = MongoRepairDocumentRepository.new_document_id()
                fingerprint = content_fingerprint(text)
                doc = RepairDocument(
                    document_id=doc_id,
                    claim_id=record.claim_id,
                    org_id=record.org_id,
                    evidence_scope="claim",
                    document_type=doc_type,
                    title=upl.get("original_filename", doc_id),
                    content=text,
                    vehicle_make=record.claim.vehicle.make,
                    vehicle_model=record.claim.vehicle.model,
                    model_year=record.claim.vehicle.model_year,
                    repair_category=record.claim.recommended_repair.repair_category,
                    verification_status=VerificationStatus.PENDING,
                    synthetic=False,
                    content_fingerprint=fingerprint,
                    vector_index_status=VectorIndexStatus.PENDING,
                    created_at=datetime.now(timezone.utc),
                )
                self._documents.insert(doc, org_id=record.org_id)
                doc_ids.append(doc_id)
                file_index[doc_id] = upl["storage_ref"]
                extracted_snippets.append(text[:2000])
                ps.documents.processed += 1
            except Exception:
                ps.documents.failed += 1
                logger.exception(
                    "Upload processing failed for claim %s file %s",
                    record.claim_id,
                    upl.get("original_filename"),
                )

        ps.documents.status = (
            StageStatus.COMPLETED if ps.documents.failed == 0 else StageStatus.FAILED
        )
        ps.touch()

        if extracted_snippets:
            self._claims.update(
                record.claim_id,
                record.org_id,
                {"extracted_findings": {"document_snippets": extracted_snippets}},
            )
        return doc_ids, file_index

    def _run_nlp(self, record, ps: ProcessingStatus):
        ps.nlp.status = StageStatus.PROCESSING
        ps.touch()
        result = None
        try:
            result = self._nlp.analyze(record.claim)
            if result.nlp_error:
                ps.nlp.status = StageStatus.FAILED
                ps.nlp.error = result.nlp_error
            else:
                ps.nlp.status = StageStatus.COMPLETED
                ps.nlp.error = None
        except Exception as exc:
            logger.exception("NLP failed for %s", record.claim_id)
            from app.modules.nlp.failure_result import build_failure_result

            result = build_failure_result(record.claim, str(exc))
            ps.nlp.status = StageStatus.FAILED
            ps.nlp.error = str(exc)[:500]
        ps.touch()
        record.nlp_analysis = result
        if result and not result.nlp_error:
            entity_count = sum(len(ext.entities) for ext in result.field_extractions)
            logger.info(
                "NLP complete for %s: pipeline=%s entities=%s",
                record.claim_id,
                result.processing_metadata.pipeline_version,
                entity_count,
            )
        return ps, result

    def _run_rag_and_tv(self, record, doc_ids: list[str], ps: ProcessingStatus, nlp_result):
        ps.rag.status = StageStatus.PROCESSING
        ps.technical_validation.status = StageStatus.PROCESSING
        ps.touch()

        rag_result: RetrievalResult | None = None
        tv_result: TechnicalValidationResult | None = None
        access = RetrievalAccessContext(org_id=record.org_id, claim_id=record.claim_id)

        try:
            self._ingest_claim_uploads(record, doc_ids)
        except Exception as exc:
            logger.warning("Claim upload ingest failed for %s: %s", record.claim_id, exc)

        if not self._settings.RAG_INVESTIGATION_ENABLED:
            ps.rag.status = StageStatus.SKIPPED
            ps.technical_validation.status = StageStatus.SKIPPED
            ps.touch()
            return ps, None, None

        try:
            self._ensure_rag_index()
            rag_result = self._rag.retrieve_for_claim(
                record.claim,
                nlp_result=nlp_result,
                run_nlp=False,
                access=access,
                top_k=self._settings.TV_DEFAULT_TOP_K,
            )
            ps.rag.status = StageStatus.COMPLETED
            ps.rag.error = None
            logger.info(
                "RAG complete for %s: passages=%s",
                record.claim_id,
                len(rag_result.passages),
            )
        except RAGNotReadyError as exc:
            ps.rag.status = StageStatus.FAILED
            ps.rag.error = str(exc)[:500]
            rag_result = RetrievalResult(query="", strategy=RetrievalStrategy.HYBRID)
        except Exception as exc:
            logger.exception("RAG failed for %s", record.claim_id)
            ps.rag.status = StageStatus.FAILED
            ps.rag.error = str(exc)[:500]
            rag_result = RetrievalResult(query="", strategy=RetrievalStrategy.HYBRID)

        if not self._settings.INVESTIGATION_RUN_TECHNICAL_VALIDATION:
            ps.technical_validation.status = StageStatus.SKIPPED
            ps.touch()
            return ps, rag_result, None

        if (
            self._settings.INVESTIGATION_SKIP_TV_IF_PRESENT
            and record.technical_validation is not None
            and rag_result is not None
            and nlp_result is not None
        ):
            from app.modules.technical_validation.fingerprint import build_input_fingerprint

            fp = build_input_fingerprint(
                record.claim,
                nlp_result,
                rag_result,
                top_k=self._settings.TV_DEFAULT_TOP_K,
            )
            if record.technical_validation.input_fingerprint == fp:
                ps.technical_validation.status = StageStatus.COMPLETED
                ps.technical_validation.error = None
                tv_result = record.technical_validation
                ps.touch()
                return ps, rag_result, tv_result

        try:
            assert nlp_result is not None
            assert rag_result is not None
            tv_result = self._tv.analyze_with_context(
                record.claim,
                nlp_result,
                rag_result,
            )
            ps.technical_validation.status = StageStatus.COMPLETED
            ps.technical_validation.error = None
        except Exception as exc:
            logger.exception("Technical validation failed for %s", record.claim_id)
            ps.technical_validation.status = StageStatus.FAILED
            ps.technical_validation.error = str(exc)[:500]

        ps.touch()
        return ps, rag_result, tv_result

    def _ingest_claim_uploads(self, record, doc_ids: list[str]) -> None:
        if not doc_ids:
            return
        min_chars = self._settings.RAG_UPLOAD_MIN_TEXT_CHARS
        for doc_id in doc_ids:
            doc = self._documents.get(doc_id, org_id=record.org_id)
            if doc is None:
                continue
            scoped = doc.model_copy(
                update={
                    "evidence_scope": "claim",
                    "org_id": record.org_id,
                    "claim_id": record.claim_id,
                }
            )
            has_vector = self._rag.has_document_in_index(doc_id)

            eligibility = assess_claim_upload_for_index(
                scoped,
                claim_id=record.claim_id,
                org_id=record.org_id,
                min_text_chars=min_chars,
                vector_store_has_document=has_vector,
            )
            now = datetime.now(timezone.utc)

            if eligibility.action == IndexAction.SKIP:
                if eligibility.reason.startswith("already indexed"):
                    continue
                self._documents.update_fields(
                    doc_id,
                    record.org_id,
                    {
                        "content_fingerprint": eligibility.fingerprint,
                        "vector_index_status": VectorIndexStatus.SKIPPED.value,
                        "vector_index_error": eligibility.reason[:500],
                        "vector_indexed_at": None,
                    },
                )
                logger.info(
                    "Skip vector index for %s on %s: %s",
                    doc_id,
                    record.claim_id,
                    eligibility.reason,
                )
                continue

            force = eligibility.action == IndexAction.REINDEX
            report = self._rag.ingest_documents([scoped], force_reindex=force)
            rec = report.records[0] if report.records else None
            if rec and rec.status == IngestStatus.INDEXED:
                self._documents.update_fields(
                    doc_id,
                    record.org_id,
                    {
                        "content_fingerprint": eligibility.fingerprint,
                        "vector_index_status": VectorIndexStatus.INDEXED.value,
                        "vector_index_error": None,
                        "vector_indexed_at": now,
                        "evidence_scope": "claim",
                    },
                )
            elif rec and rec.status == IngestStatus.SKIPPED_DUPLICATE:
                self._documents.update_fields(
                    doc_id,
                    record.org_id,
                    {
                        "content_fingerprint": eligibility.fingerprint,
                        "vector_index_status": VectorIndexStatus.INDEXED.value,
                        "vector_index_error": None,
                        "vector_indexed_at": now,
                    },
                )
            else:
                err = (rec.error if rec else None) or "unknown ingest error"
                self._documents.update_fields(
                    doc_id,
                    record.org_id,
                    {
                        "vector_index_status": VectorIndexStatus.ERROR.value,
                        "vector_index_error": err[:500],
                    },
                )

    def _ensure_rag_index(self) -> None:
        try:
            report = self._rag.ensure_startup_corpus()
            if report is not None:
                return
            count = self._rag._store.count()
        except Exception as exc:
            raise RAGNotReadyError(str(exc)) from exc
        if count > 0:
            return
        raise RAGNotReadyError(
            "Vector index is empty. Run POST /api/v1/rag/ingest first."
        )

    def _finalize_stages(self, ps: ProcessingStatus) -> ProcessingStatus:
        if ps.documents.status == StageStatus.FAILED:
            ps.overall = OverallStatus.FAILED
        elif ps.nlp.status == StageStatus.FAILED:
            ps.overall = OverallStatus.READY
        else:
            ps.overall = OverallStatus.READY
        ps.touch()
        return ps

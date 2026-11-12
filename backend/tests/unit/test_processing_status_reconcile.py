from app.schemas.processing_status import OverallStatus, ProcessingStatus, SimpleStageStatus, StageStatus
from app.services.processing_status_reconcile import reconcile_processing_status


def test_reconcile_stale_rag_empty_index_when_warm():
    ps = ProcessingStatus(
        overall=OverallStatus.FAILED,
        rag=SimpleStageStatus(
            status=StageStatus.FAILED,
            error="Vector index is empty. Run POST /api/v1/rag/ingest first.",
        ),
    )

    out = reconcile_processing_status(ps, rag_indexed=True)
    assert out.rag.status == StageStatus.COMPLETED
    assert out.rag.error is None
    assert out.overall == OverallStatus.READY


def test_reconcile_keeps_real_rag_failure():
    ps = ProcessingStatus(
        overall=OverallStatus.FAILED,
        rag=SimpleStageStatus(status=StageStatus.FAILED, error="Embedding provider timeout"),
    )

    out = reconcile_processing_status(ps, rag_indexed=True)
    assert out.rag.status == StageStatus.FAILED
    assert out.rag.error == "Embedding provider timeout"

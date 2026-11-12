"""Processing status updates when a full assessment snapshot is saved."""

from app.schemas.processing_status import OverallStatus, ProcessingStatus, StageStatus


def mark_assessment_pipeline_complete(ps: ProcessingStatus | None) -> ProcessingStatus:
    base = ps.model_copy(deep=True) if ps else ProcessingStatus()
    for stage in (
        base.nlp,
        base.rag,
        base.technical_validation,
        base.financial_validation,
        base.recommendation,
    ):
        if stage.status not in (StageStatus.SKIPPED, StageStatus.COMPLETED):
            stage.status = StageStatus.COMPLETED
            stage.error = None
    if base.documents.status == StageStatus.PENDING and base.documents.total == 0:
        base.documents.status = StageStatus.SKIPPED
    base.overall = OverallStatus.READY
    base.touch()
    return base

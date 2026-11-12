"""Pure technical validation orchestration (no I/O)."""

from app.modules.nlp.schemas import NLPAnalysisResult
from app.modules.rag.schemas import RetrievalResult
from app.modules.technical_validation.aggregation.technical_status_aggregator import (
    aggregate_technical_status,
)
from app.modules.technical_validation.complaint_diagnosis_validator import assess_complaint_diagnosis
from app.modules.technical_validation.confidence_calculator import calculate_confidence
from app.modules.technical_validation.claim_submission_evidence import (
    CLAIM_SUBMISSION_DOC_ID,
    build_claim_attested_evidence,
)
from app.modules.technical_validation.contradiction_detector import detect_contradictions
from app.modules.technical_validation.diagnostic_evidence_validator import (
    classify_retrieval,
    claim_has_measurement,
    retrieval_has_procedure_threshold,
)
from app.modules.technical_validation.evidence_quality_assessor import summarize_quality
from app.modules.technical_validation.fingerprint import build_input_fingerprint
from app.modules.technical_validation.missing_evidence_detector import detect_missing_evidence
from app.modules.technical_validation.provenance import passage_to_evidence_item
from app.modules.technical_validation.repair_justification_validator import (
    assess_repair_actions,
    assess_repair_justification,
)
from app.modules.technical_validation.repair_scope_validator import assess_repair_scope
from app.modules.technical_validation.rules.technical_rule_registry import rules_version
from app.modules.technical_validation.schemas import ValidationContext
from app.modules.technical_validation.versions import TV_PIPELINE_VERSION, TV_SCHEMA_VERSION
from app.schemas.claim import ClaimInput
from app.schemas.technical_validation import (
    EvidenceSupportClass,
    FindingType,
    TechnicalValidationResult,
    ValidationFinding,
)


def validate_technical(
    claim: ClaimInput,
    nlp: NLPAnalysisResult,
    retrieval: RetrievalResult,
    *,
    top_k: int = 5,
) -> TechnicalValidationResult:
    ctx = ValidationContext(claim=claim, nlp=nlp, retrieval=retrieval)

    ctx.complaint_diagnosis = assess_complaint_diagnosis(claim, nlp)
    ctx.repair_justification = assess_repair_justification(claim, nlp)
    ctx.classified = classify_retrieval(claim, retrieval)
    attested = build_claim_attested_evidence(claim)
    if attested:
        ctx.classified.append(attested[0])
    ctx.empty_retrieval = not retrieval.passages and attested is None
    ctx.classified, ctx.contradictions = detect_contradictions(claim, ctx.classified)

    for finding in ctx.contradictions:
        ctx.validation_findings.append(
            ValidationFinding(
                finding_type=FindingType.CONTRADICTION,
                description=finding.message,
                rule_id=finding.code,
                supporting_evidence_refs=[finding.related_document_id]
                if finding.related_document_id
                else [],
                explanation=finding.message,
            )
        )

    rag_classified = [c for c in ctx.classified if c.document_id != CLAIM_SUBMISSION_DOC_ID]
    ctx.history_only = bool(rag_classified) and all(
        c.support_class
        in (
            EvidenceSupportClass.INDIRECT_SUPPORT,
            EvidenceSupportClass.CONTEXTUAL,
        )
        for c in rag_classified
    )
    ctx.procedure_threshold_missing = retrieval_has_procedure_threshold(
        retrieval
    ) and not claim_has_measurement(claim)

    suspected = "suspect" in claim.technician_diagnosis.lower()
    ctx.missing, ctx.missing_structured = detect_missing_evidence(
        claim,
        nlp,
        retrieval,
        ctx.classified,
        consistency=ctx.complaint_diagnosis.consistency,
        suspected_only=suspected,
    )

    ctx.repair_action_assessments = assess_repair_actions(claim, nlp, ctx.classified)
    ctx.validation_findings.extend(assess_repair_scope(claim, ctx.repair_justification))

    supporting = []
    contradictory = []
    contextual = []
    for item in ctx.classified:
        ev = passage_to_evidence_item(
            item,
            evidence_type="contextual"
            if item.support_class == EvidenceSupportClass.CONTEXTUAL
            else "supporting",
        )
        if item.support_class == EvidenceSupportClass.CONTRADICTORY:
            ev.evidence_type = "contradictory"
            contradictory.append(ev)
        elif item.support_class in (
            EvidenceSupportClass.DIRECT_SUPPORT,
            EvidenceSupportClass.INDIRECT_SUPPORT,
        ):
            supporting.append(ev)
        elif item.support_class == EvidenceSupportClass.CONTEXTUAL:
            contextual.append(ev)

    ctx.supporting = supporting
    ctx.contradictory = contradictory

    ctx.evidence_quality_summary = summarize_quality(ctx.classified)
    ctx = aggregate_technical_status(ctx)
    confidence_level, confidence_score = calculate_confidence(ctx)

    diagnosis_assessment = (
        f"{ctx.complaint_diagnosis.summary} "
        f"{'Contradictions detected.' if ctx.contradictions else ''}"
    ).strip()
    footnote = (
        "Historical repairs alone do not prove the current diagnosis."
        if "R_HISTORY_ONLY" in ctx.triggered_rules
        else None
    )
    explanation = " ".join(
        filter(
            None,
            [
                f"Technical status: {ctx.suggested_status.value}.",
                *ctx.validation_reasons,
                footnote,
            ],
        )
    )

    fingerprint = build_input_fingerprint(claim, nlp, retrieval, top_k=top_k)

    return TechnicalValidationResult(
        claim_id=claim.claim_id,
        pipeline_version=TV_PIPELINE_VERSION,
        rules_version=rules_version(),
        schema_version=TV_SCHEMA_VERSION,
        input_fingerprint=fingerprint,
        technical_status=ctx.suggested_status,
        diagnosis_summary=ctx.complaint_diagnosis.summary,
        repair_assessment=ctx.repair_justification.summary,
        supporting_evidence=supporting,
        contradictory_evidence=contradictory,
        contextual_evidence=contextual,
        missing_evidence=ctx.missing,
        missing_evidence_findings=ctx.missing_structured,
        validation_findings=ctx.validation_findings,
        repair_action_assessments=ctx.repair_action_assessments,
        confidence=confidence_score,
        explanation=explanation,
        complaint_diagnosis_consistency=ctx.complaint_diagnosis.consistency,
        diagnosis_assessment=diagnosis_assessment,
        repair_justification=ctx.repair_justification.summary,
        evidence_quality=ctx.evidence_quality_summary,
        confidence_level=confidence_level,
        validation_reasons=ctx.validation_reasons,
        triggered_rules=ctx.triggered_rules,
        human_review_required=getattr(ctx, "human_review_required", True),
    )

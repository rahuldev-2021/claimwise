"""Tests for technical validation, financial validation, and recommendation schemas."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.schemas.financial_validation import FinancialStatus, FinancialValidationResult
from app.schemas.recommendation import ClaimRecommendation, OverallRecommendation
from app.schemas.repair_document import DocumentType, RepairDocument, VerificationStatus
from app.schemas.technical_validation import (
    EvidenceItem,
    TechnicalStatus,
    TechnicalValidationResult,
)


# ── RepairDocument ────────────────────────────────────────────────────────────


def test_valid_repair_document():
    doc = RepairDocument(
        document_id="DOC-001",
        document_type=DocumentType.TECHNICIAN_REPORT,
        title="Engine noise inspection",
        content="Noise confirmed at 2000 RPM.",
        created_at=datetime(2026, 9, 15, tzinfo=timezone.utc),
    )
    assert doc.verification_status == VerificationStatus.UNVERIFIED


def test_blank_document_content_rejected():
    with pytest.raises(ValueError, match="must not be blank"):
        RepairDocument(
            document_id="DOC-X",
            document_type=DocumentType.TECHNICIAN_REPORT,
            title="Test",
            content="   ",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )


def test_invalid_document_type_rejected():
    with pytest.raises(ValueError):
        RepairDocument(
            document_id="DOC-X",
            document_type="INVOICE",
            title="Test",
            content="Some content",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )


# ── TechnicalValidationResult ────────────────────────────────────────────────


def test_valid_technical_validation():
    result = TechnicalValidationResult(
        claim_id="CLM-001",
        technical_status=TechnicalStatus.QUESTIONABLE,
        diagnosis_summary="Timing chain tensioner suspected",
        repair_assessment="Engine block replacement may be excessive",
        supporting_evidence=[
            EvidenceItem(
                document_id="DOC-009",
                relevant_excerpt="Tensioner replaced. Noise resolved.",
                evidence_type="supporting",
            )
        ],
    )
    assert result.confidence is None
    assert len(result.supporting_evidence) == 1


def test_confidence_must_be_between_0_and_1():
    with pytest.raises(ValueError):
        TechnicalValidationResult(
            claim_id="CLM-X",
            technical_status=TechnicalStatus.SUPPORTED,
            diagnosis_summary="OK",
            repair_assessment="OK",
            confidence=1.5,
        )


# ── FinancialValidationResult ────────────────────────────────────────────────


def test_valid_financial_validation_minimal():
    result = FinancialValidationResult(
        claim_id="CLM-001",
        submitted_parts_cost=Decimal("4600"),
        submitted_labour_hours=Decimal("63"),
    )
    assert result.financial_status == FinancialStatus.INSUFFICIENT_DATA
    assert result.predicted_parts_cost is None


# ── ClaimRecommendation ──────────────────────────────────────────────────────


def test_valid_recommendation():
    rec = ClaimRecommendation(
        claim_id="CLM-001",
        overall_recommendation=OverallRecommendation.FLAG_FOR_REVIEW,
        recommendation_reasons=["Cost exceeds expected range", "Repair may be excessive"],
        human_review_required=True,
    )
    assert rec.human_review_required is True
    assert rec.generated_at.tzinfo is not None

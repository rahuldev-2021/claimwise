"""Tests for SampleClaimRepository."""

import pytest

from app.core.exceptions import ClaimNotFoundError, DataLoadError, DocumentNotFoundError
from app.repositories.sample_claim_repository import SampleClaimRepository


def test_load_all_claims(repository: SampleClaimRepository):
    claims = repository.list_claims()
    assert len(claims) >= 10


def test_load_all_documents(repository: SampleClaimRepository):
    docs = repository.list_documents()
    assert len(docs) >= 10


def test_get_claim_by_id(repository: SampleClaimRepository):
    claim = repository.get_claim("CLM-001")
    assert claim.claim_id == "CLM-001"
    assert claim.vehicle.make == "Ford"


def test_get_document_by_id(repository: SampleClaimRepository):
    doc = repository.get_document("DOC-001")
    assert doc.document_id == "DOC-001"


def test_missing_claim_raises(repository: SampleClaimRepository):
    with pytest.raises(ClaimNotFoundError):
        repository.get_claim("NONEXISTENT")


def test_missing_document_raises(repository: SampleClaimRepository):
    with pytest.raises(DocumentNotFoundError):
        repository.get_document("NONEXISTENT")


def test_missing_directory_raises():
    with pytest.raises(DataLoadError):
        SampleClaimRepository(data_dir="nonexistent_path")


def test_all_sample_claims_have_valid_fields(repository: SampleClaimRepository):
    for claim in repository.list_claims():
        assert claim.claim_id
        assert claim.vehicle.make
        assert claim.customer_complaint.strip()
        assert claim.submitted_parts_cost >= 0
        assert claim.submitted_labour_hours >= 0

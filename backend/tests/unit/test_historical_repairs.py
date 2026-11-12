import json
from decimal import Decimal
from pathlib import Path

import pytest

from app.schemas.historical_repair import HistoricalRepairRecord, ProvenanceKind

SAMPLE = Path(__file__).resolve().parents[2] / "data" / "sample" / "historical_repairs.json"


@pytest.fixture
def records() -> list[HistoricalRepairRecord]:
    raw = json.loads(SAMPLE.read_text(encoding="utf-8"))
    return [HistoricalRepairRecord.model_validate(r) for r in raw]


def test_no_doc008_in_historical_sources(records):
    for rec in records:
        assert "DOC-008" not in rec.source_document_ids


def test_hr010_null_claim_id(records):
    hr10 = next(r for r in records if r.historical_repair_id == "HR-010")
    assert hr10.source_claim_id is None


def test_no_recommended_as_actual_without_excerpt(records):
    for rec in records:
        if rec.actual_repair_performed and rec.recommended_repair:
            assert (
                rec.field_provenance.get("actual_repair_performed")
                and rec.field_provenance["actual_repair_performed"].provenance_kind
                != ProvenanceKind.UNAVAILABLE
            )


def test_hr002_no_inferred_recommended(records):
    hr2 = next(r for r in records if r.historical_repair_id == "HR-002")
    assert hr2.recommended_repair is None
    assert hr2.actual_repair_performed is not None


def test_derived_costs_are_derived_provenance(records):
    hr9 = next(r for r in records if r.historical_repair_id == "HR-009")
    assert hr9.parts_cost == Decimal("900")
    assert hr9.field_provenance["parts_cost"].provenance_kind == ProvenanceKind.DERIVED

from datetime import datetime, timezone

from app.schemas.historical_repair import FieldProvenance, HistoricalRepairRecord, ProvenanceKind
from app.modules.rag.historical_repair_adapter import historical_record_to_repair_document


def test_adapter_rejects_missing_explicit_provenance():
    row = HistoricalRepairRecord(
        historical_repair_id="HR-T",
        actual_repair_performed="Pads replaced",
        field_provenance={
            "actual_repair_performed": FieldProvenance(provenance_kind=ProvenanceKind.UNAVAILABLE)
        },
        verification_status="UNVERIFIED",
        synthetic=True,
        source_date=datetime.now(timezone.utc),
    )
    assert historical_record_to_repair_document(row) is None


def test_adapter_preserves_verification_and_synthetic():
    row = HistoricalRepairRecord(
        historical_repair_id="HR-T2",
        source_document_ids=["DOC-002"],
        source_claim_id="CLM-002",
        repair_category="BRAKING",
        actual_repair_performed="Pads replaced",
        repair_outcome="Noise eliminated",
        field_provenance={
            "actual_repair_performed": FieldProvenance(
                provenance_kind=ProvenanceKind.EXPLICIT,
                document_id="DOC-002",
                excerpt="Pads replaced",
            )
        },
        verification_status="VERIFIED",
        synthetic=True,
        source_date=datetime.now(timezone.utc),
    )
    doc = historical_record_to_repair_document(row)
    assert doc is not None
    assert doc.synthetic is True
    assert doc.verification_status.value == "VERIFIED"
    assert doc.source_document_ids == "DOC-002"
    assert doc.historical_repair_id == "HR-T2"
    assert doc.evidence_scope == "global"

"""Convert approved historical repair records into RAG RepairDocument entries."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import Settings
from app.schemas.historical_repair import HistoricalRepairRecord, ProvenanceKind
from app.schemas.repair_document import DocumentType, RepairDocument, VerificationStatus


def _load_historical_rows(settings: Settings) -> list[HistoricalRepairRecord]:
    if not settings.HISTORICAL_REPAIRS_INGEST_ENABLED:
        return []
    path = Path(settings.SAMPLE_DATA_DIR) / "historical_repairs.json"
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [HistoricalRepairRecord.model_validate(item) for item in raw]


def persist_historical_rows_to_mongo(db, settings: Settings) -> int:
    """Write approved historical rows to Mongo when ingest is explicitly enabled."""
    rows = _load_historical_rows(settings)
    if not rows or db is None:
        return 0
    from app.repositories.mongo_historical_repair_repository import (
        MongoHistoricalRepairRepository,
    )

    return MongoHistoricalRepairRepository(db).upsert_many(rows)


def load_historical_as_documents(settings: Settings) -> list[RepairDocument]:
    rows = _load_historical_rows(settings)
    out: list[RepairDocument] = []
    for row in rows:
        doc = historical_record_to_repair_document(row)
        if doc is not None:
            out.append(doc)
    return out


def historical_record_to_repair_document(
    row: HistoricalRepairRecord,
) -> RepairDocument | None:
    actual = (row.actual_repair_performed or "").strip()
    if not actual:
        return None
    prov = row.field_provenance.get("actual_repair_performed")
    if prov is not None and prov.provenance_kind != ProvenanceKind.EXPLICIT:
        return None

    parts = [
        f"Historical repair {row.historical_repair_id} (synthetic={row.synthetic}).",
        f"Complaint: {row.customer_complaint or ''}".strip(),
        f"Diagnosis: {row.technician_diagnosis or ''}".strip(),
        f"Actual repair performed: {actual}",
        f"Outcome: {row.repair_outcome or ''}".strip(),
    ]
    content = "\n".join(p for p in parts if p)

    try:
        status = VerificationStatus(row.verification_status.upper())
    except ValueError:
        status = VerificationStatus.UNVERIFIED

    source_ids = ",".join(row.source_document_ids) if row.source_document_ids else None
    created = row.source_date or datetime.now(timezone.utc)

    return RepairDocument(
        document_id=f"HIST-{row.historical_repair_id}",
        claim_id=row.source_claim_id,
        document_type=DocumentType.REPAIR_HISTORY,
        title=f"Historical repair {row.historical_repair_id}",
        content=content,
        vehicle_make=row.vehicle_make,
        vehicle_model=row.vehicle_model,
        model_year=row.model_year,
        repair_category=row.repair_category,
        verification_status=status,
        evidence_scope="global",
        synthetic=row.synthetic,
        source_document_ids=source_ids,
        historical_repair_id=row.historical_repair_id,
        created_at=created,
    )

"""Metadata extraction for RAG indexing."""

from app.modules.rag.evidence_source import resolve_evidence_source_type
from app.schemas.repair_document import RepairDocument

_OPTIONAL_FIELDS: tuple[str, ...] = (
    "claim_id",
    "document_type",
    "vehicle_make",
    "vehicle_model",
    "model_year",
    "repair_category",
    "part_number",
    "repair_outcome",
    "verification_status",
    "evidence_scope",
    "org_id",
    "synthetic",
    "component",
    "source_document_ids",
    "historical_repair_id",
)


def _resolve_evidence_scope(doc: RepairDocument) -> str:
    if doc.evidence_scope:
        return doc.evidence_scope.strip().lower()
    if doc.claim_id:
        return "claim"
    return "global"


def extract_metadata(doc: RepairDocument) -> dict[str, object]:
    """Return a scalar metadata dict safe for the vector store."""
    meta: dict[str, object] = {"document_id": doc.document_id}
    scope = _resolve_evidence_scope(doc)
    meta["evidence_scope"] = scope
    meta["evidence_source_type"] = resolve_evidence_source_type(evidence_scope=scope)

    for field in _OPTIONAL_FIELDS:
        value = getattr(doc, field)
        if value is None:
            continue
        if hasattr(value, "value"):
            value = value.value
        meta[field] = value

    if scope == "claim":
        if not doc.org_id or not doc.claim_id:
            raise ValueError(
                f"claim-scoped document {doc.document_id} requires org_id and claim_id"
            )
        meta["org_id"] = doc.org_id
        meta["claim_id"] = doc.claim_id
    elif "claim_id" in meta and meta.get("claim_id"):
        meta.pop("claim_id", None)

    meta["created_at"] = doc.created_at.isoformat()
    meta["synthetic"] = bool(doc.synthetic)
    return meta

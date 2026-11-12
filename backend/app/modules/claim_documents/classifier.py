"""Heuristic document type classification."""

from app.schemas.repair_document import DocumentType


def classify_document_text(text: str, filename: str) -> DocumentType:
    lower = (text + " " + filename).lower()
    if any(k in lower for k in ("dtc", "diagnostic", "scan tool", "obd")):
        return DocumentType.DIAGNOSTIC_REPORT
    if any(k in lower for k in ("invoice", "parts", "cost")):
        return DocumentType.PART_REFERENCE
    if any(k in lower for k in ("labour", "labor", "hours")):
        return DocumentType.LABOUR_REFERENCE
    if any(k in lower for k in ("history", "previous repair")):
        return DocumentType.REPAIR_HISTORY
    return DocumentType.TECHNICIAN_REPORT

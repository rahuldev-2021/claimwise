import pytest

from app.modules.claim_documents.security import validate_upload


def test_rejects_non_pdf_magic():
    with pytest.raises(ValueError, match="valid PDF"):
        validate_upload("report.pdf", b"NOTPDF", max_file_bytes=1_000_000)


def test_accepts_minimal_pdf_header():
    validated = validate_upload("a.pdf", b"%PDF-1.4\n", max_file_bytes=1_000_000)
    assert validated.detected_kind == "pdf"


def test_rejects_bad_extension():
    with pytest.raises(ValueError, match="Only .pdf"):
        validate_upload("evil.exe", b"%PDF-", max_file_bytes=1_000_000)

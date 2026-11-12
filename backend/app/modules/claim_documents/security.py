"""Upload validation: magic bytes, extensions, ZIP bomb limits."""

import io
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

PDF_SIG = b"%PDF"
ZIP_SIG = b"PK\x03\x04"
ALLOWED_EXT = {".pdf", ".docx"}
MAX_ZIP_ENTRIES = 200
MAX_UNCOMPRESSED = 25 * 1024 * 1024


@dataclass
class ValidatedUpload:
    original_filename: str
    safe_filename: str
    content: bytes
    detected_kind: str  # pdf | docx


def sanitize_filename(name: str) -> str:
    base = Path(name).name
    base = re.sub(r"[^\w.\-]", "_", base)
    if ".." in base or base.startswith("."):
        raise ValueError("Invalid filename")
    return base[:200]


def validate_upload(filename: str, content: bytes, *, max_file_bytes: int) -> ValidatedUpload:
    if len(content) > max_file_bytes:
        raise ValueError(f"File exceeds maximum size ({max_file_bytes} bytes)")
    safe = sanitize_filename(filename)
    ext = Path(safe).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise ValueError("Only .pdf and .docx files are allowed")
    if ext == ".pdf":
        if not content.startswith(PDF_SIG):
            raise ValueError("File is not a valid PDF")
        return ValidatedUpload(safe, safe, content, "pdf")
    if not content.startswith(ZIP_SIG):
        raise ValueError("File is not a valid DOCX")
    _check_docx_zip(content)
    return ValidatedUpload(safe, safe, content, "docx")


def _check_docx_zip(content: bytes) -> None:
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        total = 0
        if len(zf.namelist()) > MAX_ZIP_ENTRIES:
            raise ValueError("DOCX archive has too many entries")
        for info in zf.infolist():
            total += info.file_size
            if total > MAX_UNCOMPRESSED:
                raise ValueError("DOCX uncompressed size too large")

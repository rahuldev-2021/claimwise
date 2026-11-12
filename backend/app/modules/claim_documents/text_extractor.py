"""Extract plain text from PDF and DOCX uploads."""

import io
import zipfile
import xml.etree.ElementTree as ET

from pypdf import PdfReader


def extract_text_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        parts.append(text.strip())
    return "\n\n".join(p for p in parts if p)


def extract_text_docx(content: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    texts: list[str] = []
    for node in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
        if node.text:
            texts.append(node.text)
    return " ".join(texts).strip()


def extract_text(kind: str, content: bytes) -> str:
    if kind == "pdf":
        return extract_text_pdf(content)
    if kind == "docx":
        return extract_text_docx(content)
    raise ValueError(f"Unsupported kind: {kind}")

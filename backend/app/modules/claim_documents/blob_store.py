"""Private filesystem blob storage (dev)."""

import hashlib
from pathlib import Path
from uuid import uuid4

from app.core.config import Settings


class LocalBlobStore:
    def __init__(self, settings: Settings) -> None:
        self._root = Path(settings.CLAIMS_UPLOAD_DIR)
        self._root.mkdir(parents=True, exist_ok=True)

    def save(self, claim_id: str, content: bytes, *, suffix: str = ".bin") -> dict:
        claim_dir = self._root / claim_id
        claim_dir.mkdir(parents=True, exist_ok=True)
        name = f"{uuid4().hex}{suffix}"
        path = claim_dir / name
        path.write_bytes(content)
        return {
            "storage_ref": str(path.relative_to(self._root)),
            "sha256": hashlib.sha256(content).hexdigest(),
            "size_bytes": len(content),
        }

    def read(self, storage_ref: str) -> bytes:
        path = self._root / storage_ref
        if not path.resolve().is_relative_to(self._root.resolve()):
            raise ValueError("Invalid storage reference")
        return path.read_bytes()

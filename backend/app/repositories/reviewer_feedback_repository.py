"""JSON-file persistence for reviewer feedback (development scope, not a production store)."""

import json
import logging
import threading
from pathlib import Path

from app.core.exceptions import DataLoadError
from app.schemas.reviewer_feedback import ReviewerFeedback

logger = logging.getLogger(__name__)


class ReviewerFeedbackRepository:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._lock = threading.Lock()

    def _read_all(self) -> list[ReviewerFeedback]:
        if not self._path.exists():
            return []
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            return [ReviewerFeedback.model_validate(item) for item in raw]
        except (json.JSONDecodeError, OSError, ValueError) as exc:
            raise DataLoadError(str(self._path), str(exc)) from exc

    def add(self, feedback: ReviewerFeedback) -> ReviewerFeedback:
        with self._lock:
            records = self._read_all()
            records.append(feedback)
            self._path.parent.mkdir(parents=True, exist_ok=True)
            payload = [r.model_dump(mode="json") for r in records]
            self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        logger.info("Stored reviewer feedback for claim %s", feedback.claim_id)
        return feedback

    def list_for_claim(self, claim_id: str) -> list[ReviewerFeedback]:
        with self._lock:
            records = self._read_all()
        return [r for r in records if r.claim_id == claim_id]

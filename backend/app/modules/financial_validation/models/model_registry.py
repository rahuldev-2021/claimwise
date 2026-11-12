"""Trusted model registry with schema compatibility checks."""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional

InferenceMode = Literal["production", "experimental"]

from app.modules.financial_validation.exceptions import FinancialModelError

TaskName = Literal["parts_cost", "labour_hours"]
RegistryStatus = Literal["stub", "trained"]
RegistryLifecycle = Literal["production", "validation", "experimental"]
REGISTRY_FILENAME = "registry.json"


@dataclass
class ModelRegistryEntry:
    task: TaskName
    version: str
    model_path: str
    preprocessor_path: str
    feature_schema_hash: str
    sklearn_version: str
    training_data_version: str
    evaluation_strategy: str
    metrics: dict[str, Any]
    status: RegistryStatus
    trusted: bool = True
    trained_at: str = ""
    lifecycle: RegistryLifecycle = "production"
    synthetic_data: bool = False
    production_ready: bool = False
    algorithm: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelRegistryEntry":
        return cls(
            task=data["task"],
            version=data["version"],
            model_path=data["model_path"],
            preprocessor_path=data["preprocessor_path"],
            feature_schema_hash=data["feature_schema_hash"],
            sklearn_version=data.get("sklearn_version", ""),
            training_data_version=data.get("training_data_version", ""),
            evaluation_strategy=data.get("evaluation_strategy", ""),
            metrics=data.get("metrics", {}),
            status=data.get("status", "stub"),
            trusted=data.get("trusted", True),
            trained_at=data.get("trained_at", ""),
            lifecycle=data.get("lifecycle", "production"),
            synthetic_data=bool(data.get("synthetic_data", False)),
            production_ready=bool(
                data["production_ready"]
                if "production_ready" in data
                else data.get("status") == "trained" and not data.get("synthetic_data", False)
            ),
            algorithm=data.get("algorithm", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "version": self.version,
            "model_path": self.model_path,
            "preprocessor_path": self.preprocessor_path,
            "feature_schema_hash": self.feature_schema_hash,
            "sklearn_version": self.sklearn_version,
            "training_data_version": self.training_data_version,
            "evaluation_strategy": self.evaluation_strategy,
            "metrics": self.metrics,
            "status": self.status,
            "trusted": self.trusted,
            "trained_at": self.trained_at or datetime.now(timezone.utc).isoformat(),
            "lifecycle": self.lifecycle,
            "synthetic_data": self.synthetic_data,
            "production_ready": self.production_ready,
            "algorithm": self.algorithm,
        }

    def eligible_for_inference(self) -> bool:
        """Production inference only (never synthetic experimental)."""
        if not self.trusted:
            return False
        if self.status != "trained":
            return False
        if self.lifecycle == "experimental":
            return False
        if self.lifecycle == "validation":
            return True
        if self.lifecycle == "production":
            return self.production_ready
        return False

    def eligible_for_experimental_inference(self) -> bool:
        """Explicit experimental mode — synthetic Gate 2 artifacts only."""
        if not self.trusted or self.status != "trained":
            return False
        return self.lifecycle == "experimental" and self.synthetic_data and not self.production_ready


def feature_schema_hash(feature_ids: list[str]) -> str:
    payload = json.dumps(sorted(feature_ids), separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


class ModelRegistry:
    def __init__(self, root: str | Path, *, trusted_root_only: bool = True) -> None:
        self.root = Path(root).resolve()
        self.trusted_root_only = trusted_root_only
        self.root.mkdir(parents=True, exist_ok=True)

    @property
    def registry_path(self) -> Path:
        return self.root / REGISTRY_FILENAME

    def load(self) -> list[ModelRegistryEntry]:
        if not self.registry_path.is_file():
            return []
        data = json.loads(self.registry_path.read_text(encoding="utf-8"))
        entries = data.get("entries") or []
        return [ModelRegistryEntry.from_dict(e) for e in entries]

    def save(self, entries: list[ModelRegistryEntry]) -> None:
        payload = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "entries": [e.to_dict() for e in entries],
        }
        self.registry_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _resolve_artifact(self, rel_path: str) -> Path:
        path = (self.root / rel_path).resolve()
        if self.trusted_root_only:
            try:
                path.relative_to(self.root)
            except ValueError as exc:
                raise FinancialModelError(f"Untrusted model path outside registry: {rel_path}") from exc
        if not path.is_file():
            raise FinancialModelError(f"Model artifact missing: {rel_path}")
        return path

    def get_active_entry(
        self,
        task: TaskName,
        *,
        expected_schema_hash: Optional[str] = None,
        inference_mode: InferenceMode = "production",
    ) -> Optional[ModelRegistryEntry]:
        if inference_mode == "experimental":
            eligible = lambda e: e.eligible_for_experimental_inference()  # noqa: E731
        else:
            eligible = lambda e: e.eligible_for_inference()  # noqa: E731
        entries = [e for e in self.load() if e.task == task and eligible(e)]
        if not entries:
            return None
        entry = sorted(entries, key=lambda e: e.version)[-1]
        if expected_schema_hash and entry.feature_schema_hash != expected_schema_hash:
            raise FinancialModelError(
                f"Feature schema mismatch for {task}: registry {entry.feature_schema_hash} "
                f"!= config {expected_schema_hash}"
            )
        for rel in (entry.model_path, entry.preprocessor_path):
            self._resolve_artifact(rel)
        return entry

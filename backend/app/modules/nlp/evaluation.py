"""Offline NLP evaluation harness (CLI-first)."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.modules.nlp.pipeline import NLPPipeline
from app.modules.nlp.versions import PIPELINE_VERSION, abbreviation_dict_version
from app.modules.nlp.taxonomy_data import TAXONOMY_VERSION
from app.schemas.claim import ClaimInput


@dataclass
class EvaluationRunReport:
    dataset_version: str
    dataset_split_config: str
    pipeline_version: str
    taxonomy_version: str
    abbreviation_dict_version: str
    evaluation_timestamp: str
    metrics_overall: dict[str, float]
    metrics_by_entity_category: dict[str, dict[str, float]]
    metrics_by_scenario: dict[str, dict[str, float]]
    synthetic_vs_real: dict[str, dict[str, float]]

    def to_json(self) -> dict[str, Any]:
        return {
            "dataset_version": self.dataset_version,
            "dataset_split_config": self.dataset_split_config,
            "pipeline_version": self.pipeline_version,
            "taxonomy_version": self.taxonomy_version,
            "abbreviation_dict_version": self.abbreviation_dict_version,
            "evaluation_timestamp": self.evaluation_timestamp,
            "metrics_overall": self.metrics_overall,
            "metrics_by_entity_category": self.metrics_by_entity_category,
            "metrics_by_scenario": self.metrics_by_scenario,
            "synthetic_vs_real": self.synthetic_vs_real,
        }


def _dataset_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _load_claims(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_evaluation(
    dataset_path: Path,
    *,
    split_config: str = "default",
    expect_dataset_version: str | None = None,
    modes: str = "deterministic",
) -> EvaluationRunReport:
    version = _dataset_hash(dataset_path)
    if expect_dataset_version and expect_dataset_version != version:
        raise ValueError(
            f"Dataset version mismatch: expected {expect_dataset_version}, got {version}"
        )

    from app.core.config import Settings
    from app.modules.nlp.pipeline_factory import build_nlp_pipeline

    settings = Settings()
    mode_list = [m.strip() for m in modes.split(",") if m.strip()]
    if "llm_fallback" in mode_list:
        settings = settings.model_copy(update={"LLM_NLP_ENABLED": True})
    pipeline = build_nlp_pipeline(settings) if "llm_fallback" in mode_list else NLPPipeline()
    tp = fp = fn = 0
    by_category: dict[str, dict[str, int]] = {}
    by_scenario: dict[str, dict[str, int]] = {}
    synthetic_block = {"tp": 0, "fp": 0, "fn": 0}
    real_block = {"tp": 0, "fp": 0, "fn": 0}

    for row in _load_claims(dataset_path):
        claim = ClaimInput.model_validate(row["claim"])
        labels = row.get("expected_entities", [])
        scenario = row.get("scenario", "general")
        label_source = row.get("label_source", "synthetic")
        result = pipeline.analyze(claim)
        predicted = {
            (e.category.value, e.canonical)
            for ext in result.field_extractions
            for e in ext.entities
            if e.entity_id
        }
        expected = {(e["category"], e["canonical"]) for e in labels}
        hits = predicted & expected
        tp += len(hits)
        fp += len(predicted - expected)
        fn += len(expected - predicted)
        block = synthetic_block if label_source == "synthetic" else real_block
        block["tp"] += len(hits)
        block["fp"] += len(predicted - expected)
        block["fn"] += len(expected - predicted)
        for cat, _ in expected:
            by_category.setdefault(cat, {"tp": 0, "fp": 0, "fn": 0})
        for cat, can in predicted:
            bucket = by_category.setdefault(cat, {"tp": 0, "fp": 0, "fn": 0})
            if (cat, can) in expected:
                bucket["tp"] += 1
            else:
                bucket["fp"] += 1
        for cat, can in expected - predicted:
            by_category.setdefault(cat, {"tp": 0, "fp": 0, "fn": 0})["fn"] += 1
        by_scenario.setdefault(scenario, {"tp": 0, "fp": 0, "fn": 0})
        by_scenario[scenario]["tp"] += len(hits)
        by_scenario[scenario]["fp"] += len(predicted - expected)
        by_scenario[scenario]["fn"] += len(expected - predicted)

    def prf(counts: dict[str, int]) -> dict[str, float]:
        p = counts["tp"] / (counts["tp"] + counts["fp"]) if counts["tp"] + counts["fp"] else 0.0
        r = counts["tp"] / (counts["tp"] + counts["fn"]) if counts["tp"] + counts["fn"] else 0.0
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4)}

    return EvaluationRunReport(
        dataset_version=version,
        dataset_split_config=split_config,
        pipeline_version=PIPELINE_VERSION,
        taxonomy_version=TAXONOMY_VERSION,
        abbreviation_dict_version=abbreviation_dict_version(),
        evaluation_timestamp=datetime.now(timezone.utc).isoformat(),
        metrics_overall=prf({"tp": tp, "fp": fp, "fn": fn}),
        metrics_by_entity_category={k: prf(v) for k, v in by_category.items()},
        metrics_by_scenario={k: prf(v) for k, v in by_scenario.items()},
        synthetic_vs_real={
            "synthetic": prf(synthetic_block),
            "real": prf(real_block),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run NLP evaluation harness")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/nlp/evaluation_entities.jsonl"),
    )
    parser.add_argument("--split-config", default="claim_holdout_dev")
    parser.add_argument("--expect-dataset-version", default=None)
    parser.add_argument("--output", type=Path, default=Path("data/nlp/reports/latest_evaluation.json"))
    parser.add_argument(
        "--modes",
        default="deterministic",
        help="Comma-separated: deterministic,spacy,llm_fallback",
    )
    args = parser.parse_args()
    report = run_evaluation(
        args.dataset,
        split_config=args.split_config,
        expect_dataset_version=args.expect_dataset_version,
        modes=args.modes,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = report.to_json()
    if "evaluation_modes" not in payload:
        payload["evaluation_modes"] = [m.strip() for m in args.modes.split(",")]
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

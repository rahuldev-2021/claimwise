from pathlib import Path

from app.modules.nlp.evaluation import run_evaluation

DATASET = Path(__file__).resolve().parents[2] / "data" / "nlp" / "evaluation_entities.jsonl"


def test_evaluation_run_produces_report():
    report = run_evaluation(DATASET, split_config="dev")
    assert report.pipeline_version == "0.4.0"
    assert "precision" in report.metrics_overall
    assert report.synthetic_vs_real["synthetic"]["f1"] >= 0.0

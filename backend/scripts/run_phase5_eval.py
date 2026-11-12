"""Mock-provider Phase 5 eval harness (CI-safe). Use --live for real providers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.core.config import Settings
from app.repositories.sample_claim_repository import SampleClaimRepository
from app.services.assessment_service import AssessmentService


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Use configured LLM provider (not mock)")
    parser.add_argument("--scenarios", default="data/llm/phase5_eval_scenarios.json")
    args = parser.parse_args()

    settings = Settings()
    if not args.live:
        settings = settings.model_copy(update={"LLM_ENABLED": True, "LLM_PROVIDER": "mock"})

    scenarios = json.loads(Path(args.scenarios).read_text(encoding="utf-8"))
    repo = SampleClaimRepository(data_dir=settings.SAMPLE_DATA_DIR)
    service = AssessmentService.for_tests(settings)

    results = []
    for scenario in scenarios:
        claim = repo.get_claim(scenario["claim_id"])
        out = service.analyze_claim(claim, top_k=3, financial_enabled=False)
        results.append(
            {
                "scenario_id": scenario["id"],
                "llm_status": out.llm_execution.status.value,
                "recommendation": out.recommendation.overall_recommendation.value,
                "structured_valid": out.llm_contextual_assessment is not None,
            }
        )

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

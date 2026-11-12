from datetime import datetime, timezone
from decimal import Decimal

from app.modules.nlp.contextual_extraction import ContextualExtractionProvider
from app.modules.nlp.pipeline import NLPPipeline
from app.modules.nlp.schemas import NLPAnalysisResult
from app.schemas.claim import ClaimInput
from app.schemas.repair import Repair
from app.schemas.vehicle import Vehicle


class _IdentityProvider:
    def enrich(self, claim: ClaimInput, deterministic: NLPAnalysisResult) -> NLPAnalysisResult:
        return deterministic


class _TaggingProvider:
    def enrich(self, claim: ClaimInput, deterministic: NLPAnalysisResult) -> NLPAnalysisResult:
        structured = deterministic.structured_extraction.model_copy(
            update={"component": "hook_called"}
        )
        return deterministic.model_copy(update={"structured_extraction": structured})


def _minimal_claim() -> ClaimInput:
    return ClaimInput(
        claim_id="CTX-1",
        submission_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        vehicle=Vehicle(vehicle_id="V1", make="Ford", model="Focus", model_year=2020),
        customer_complaint="engine noise",
        technician_diagnosis="inspect engine",
        recommended_repair=Repair(
            repair_category="ENGINE",
            part_description="n/a",
            recommended_action="inspect",
        ),
        submitted_parts_cost=Decimal("0"),
        submitted_labour_hours=Decimal("1"),
    )


def test_contextual_provider_protocol():
    assert isinstance(_IdentityProvider(), ContextualExtractionProvider)


def test_pipeline_without_contextual_unchanged():
    result = NLPPipeline().analyze(_minimal_claim())
    assert result.structured_extraction.component == "engine"


def test_pipeline_with_contextual_hook():
    result = NLPPipeline(contextual=_TaggingProvider()).analyze(_minimal_claim())
    assert result.structured_extraction.component == "hook_called"

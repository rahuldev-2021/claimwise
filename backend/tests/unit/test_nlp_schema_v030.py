from app.modules.nlp.pipeline import NLPPipeline
from app.modules.nlp.schemas import (
    EntityCategory,
    EntityRelationship,
    ExtractionMethod,
    ExtractedEntity,
    FieldExtraction,
    NLPAnalysisResult,
    RelationshipPredicate,
    TextSourceField,
)
from app.repositories.sample_claim_repository import SampleClaimRepository
from tests.conftest import SAMPLE_DATA_DIR


def test_pipeline_entity_ids_and_relationship_refs():
    repo = SampleClaimRepository(SAMPLE_DATA_DIR)
    claim = repo.get_claim("CLM-001")
    result = NLPPipeline().analyze(claim)
    ids = [e.entity_id for ext in result.field_extractions for e in ext.entities]
    assert all(ids)
    assert len(ids) == len(set(ids))
    for rel in result.entity_relationships:
        assert rel.subject_entity_id in ids or rel.subject_entity_id in [
            e.entity_id for e in result.recommended_repair.entities
        ]


def test_repair_alignment_hints_require_validation():
    repo = SampleClaimRepository(SAMPLE_DATA_DIR)
    result = NLPPipeline().analyze(repo.get_claim("CLM-001"))
    assert all(h.requires_validation for h in result.repair_alignment_hints)


def test_nlp_result_validator_rejects_bad_relationship():
    ent_a = ExtractedEntity(
        entity_id="ENT-001",
        text="noise",
        canonical="abnormal_noise",
        category=EntityCategory.SYMPTOM,
        source_field=TextSourceField.CUSTOMER_COMPLAINT,
    )
    ent_b = ExtractedEntity(
        entity_id="ENT-002",
        text="engine",
        canonical="engine",
        category=EntityCategory.COMPONENT,
        source_field=TextSourceField.CUSTOMER_COMPLAINT,
    )
    try:
        NLPAnalysisResult(
            claim_id="X",
            original_complaint="a",
            original_diagnosis="b",
            normalized_complaint="a",
            normalized_diagnosis="b",
            field_extractions=[
                FieldExtraction(
                    source_field=TextSourceField.CUSTOMER_COMPLAINT,
                    entities=[ent_a, ent_b],
                )
            ],
            recommended_repair=__import__(
                "app.modules.nlp.schemas", fromlist=["RecommendedRepairExtraction"]
            ).RecommendedRepairExtraction(
                repair_category="ENGINE",
                part_description="x",
                recommended_action="replace",
            ),
            complaint_diagnosis_comparison=__import__(
                "app.modules.nlp.schemas", fromlist=["ComplaintDiagnosisComparison"]
            ).ComplaintDiagnosisComparison(),
            structured_extraction=__import__(
                "app.modules.nlp.schemas", fromlist=["StructuredExtraction"]
            ).StructuredExtraction(),
            processing_metadata=__import__(
                "app.modules.nlp.schemas", fromlist=["ProcessingMetadata"]
            ).ProcessingMetadata(),
            entity_relationships=[
                EntityRelationship(
                    relationship_id="REL-1",
                    subject_entity_id="ENT-001",
                    predicate=RelationshipPredicate.LOCATED_AT,
                    object_entity_id="ENT-999",
                    source_field=TextSourceField.CUSTOMER_COMPLAINT,
                    source_text="noise from engine",
                    confidence=0.8,
                    extraction_method=ExtractionMethod.RULE_BASED,
                )
            ],
        )
        assert False, "expected validation error"
    except ValueError:
        pass

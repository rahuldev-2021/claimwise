"""Regression tests for CLM-0005-style braking claim NLP quality."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.modules.nlp.entity_confidence import is_confirmed_entity
from app.modules.nlp.entity_extractor import spacy_available
from app.modules.nlp.pipeline import NLPPipeline
from app.modules.nlp.schemas import EntityCategory, ExtractionMethod, TextSourceField
from app.schemas.claim import ClaimInput, ClaimStatus
from app.schemas.repair import Repair
from app.schemas.vehicle import Vehicle


def _braking_claim() -> ClaimInput:
    text = (
        "Replace front brake pads and resurface rotors. "
        "Verify caliper slide pins and flush brake fluid if contaminated."
    )
    return ClaimInput(
        claim_id="CLM-TEST-BRAKE",
        submission_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        vehicle=Vehicle(
            vehicle_id="V-1",
            make="Ford",
            model="F-150",
            model_year=2023,
        ),
        customer_complaint=(
            "Squealing noise from the front wheels when braking at low speed. "
            "Customer reports the sound started after 28,000 miles."
        ),
        technician_diagnosis=(
            "Front pads below minimum thickness; rotors glazed with heat spots. "
            "Caliper slides move freely; no hydraulic fault found on road test."
        ),
        recommended_repair=Repair(
            repair_category="BRAKING",
            part_description=text,
            recommended_action=text,
        ),
        submitted_parts_cost=Decimal("320"),
        submitted_labour_hours=Decimal("2.5"),
        claim_status=ClaimStatus.SUBMITTED,
    )


def test_repair_text_not_duplicated():
    claim = _braking_claim()
    result = NLPPipeline().analyze(claim)
    assert result.normalized_repair.count("replace front brake pads") == 1


def test_no_braking_system_from_when_braking():
    claim = _braking_claim()
    result = NLPPipeline().analyze(claim)
    complaint = next(
        e for e in result.field_extractions if e.source_field == TextSourceField.CUSTOMER_COMPLAINT
    )
    assert not any(
        e.category == EntityCategory.COMPONENT and e.canonical == "braking_system"
        for e in complaint.entities
    )


def test_diagnosis_findings_and_part_match_hint():
    claim = _braking_claim()
    result = NLPPipeline().analyze(claim)
    diagnosis = next(
        e for e in result.field_extractions if e.source_field == TextSourceField.TECHNICIAN_DIAGNOSIS
    )
    assert any(e.category == EntityCategory.DIAGNOSTIC_FINDING for e in diagnosis.entities)
    assert any(
        h.type.value == "component_reference_match" for h in result.repair_alignment_hints
    )
    missing_diag_hint = any(
        h.type.value == "missing_diagnostic_finding_in_submitted_diagnosis"
        for h in result.repair_alignment_hints
    )
    assert not missing_diag_hint


def test_no_braking_system_inside_brake_pads_phrase():
    claim = _braking_claim()
    result = NLPPipeline().analyze(claim)
    repair_ents = result.recommended_repair.entities
    assert not any(
        e.category == EntityCategory.COMPONENT and e.canonical == "braking_system"
        for e in repair_ents
    )


def test_no_failure_mode_on_repair_fluid_contaminated():
    claim = _braking_claim()
    result = NLPPipeline().analyze(claim)
    repair_ents = result.recommended_repair.entities
    assert not any(e.category == EntityCategory.FAILURE_MODE for e in repair_ents)


def test_repair_relationships_are_local_not_cartesian():
    claim = _braking_claim()
    result = NLPPipeline().analyze(claim)
    repair_rels = [
        r
        for r in result.entity_relationships
        if r.source_field == TextSourceField.RECOMMENDED_REPAIR
        and r.predicate.value == "recommends"
    ]
    assert len(repair_rels) <= 4
    replace_id = next(
        e.entity_id for e in result.recommended_repair.entities if e.canonical == "replace"
    )
    resurface_id = next(
        e.entity_id for e in result.recommended_repair.entities if e.canonical == "resurface"
    )
    rotor_id = next(
        e.entity_id for e in result.recommended_repair.entities if e.canonical == "brake_rotor"
    )
    pad_id = next(
        e.entity_id for e in result.recommended_repair.entities if e.canonical == "brake_pad"
    )
    assert any(
        r.subject_entity_id == replace_id and r.object_entity_id == pad_id for r in repair_rels
    )
    assert any(
        r.subject_entity_id == resurface_id and r.object_entity_id == rotor_id for r in repair_rels
    )
    assert not any(
        r.subject_entity_id == replace_id and r.object_entity_id == rotor_id for r in repair_rels
    )


def test_repair_original_text_excludes_category_and_spans_match_narrative():
    claim = _braking_claim()
    result = NLPPipeline().analyze(claim)
    action = claim.recommended_repair.recommended_action
    assert result.original_repair.startswith(action[:20])
    assert not result.original_repair.strip().upper().startswith("BRAKING")
    repair_ents = result.recommended_repair.entities
    for ent in repair_ents:
        if ent.span_start is None or ent.span_end is None:
            continue
        slice_ = result.original_repair[ent.span_start : ent.span_end]
        assert ent.source_text.casefold() == slice_.casefold()


def test_hydraulic_fault_ruled_out_is_negated():
    claim = _braking_claim()
    result = NLPPipeline().analyze(claim)
    diagnosis = next(
        e for e in result.field_extractions if e.source_field == TextSourceField.TECHNICIAN_DIAGNOSIS
    )
    hydraulic = next(
        e for e in diagnosis.entities if e.canonical == "hydraulic_fault"
    )
    assert hydraulic.negated is True
    assert hydraulic.category == EntityCategory.FAILURE_MODE


def test_diagnosis_finding_spans_not_nested_duplicates():
    claim = _braking_claim()
    result = NLPPipeline().analyze(claim)
    diagnosis = next(
        e for e in result.field_extractions if e.source_field == TextSourceField.TECHNICIAN_DIAGNOSIS
    )
    assert any(e.canonical == "pad_thickness_low" for e in diagnosis.entities)
    assert not any(e.canonical == "below_minimum_thickness" for e in diagnosis.entities)


def test_symptom_onset_mileage_not_current_odometer():
    claim = _braking_claim()
    result = NLPPipeline().analyze(claim)
    complaint = next(
        e for e in result.field_extractions if e.source_field == TextSourceField.CUSTOMER_COMPLAINT
    )
    mileage = next(e for e in complaint.entities if e.category.value == "measurement")
    assert mileage.canonical == "symptom_onset_mileage"
    assert any(m.code == "SYMPTOM_ONSET_MILEAGE_IN_NARRATIVE" for m in result.missing_information)


def test_diagnosis_condition_relationships():
    claim = _braking_claim()
    result = NLPPipeline().analyze(claim)
    diag_rels = [
        r for r in result.entity_relationships if r.source_field == TextSourceField.TECHNICIAN_DIAGNOSIS
    ]
    assert any(r.predicate.value == "affects" for r in diag_rels)
    entities = {
        e.entity_id: e
        for ext in result.field_extractions
        for e in ext.entities
    }
    caliper_free = next(
        e.entity_id
        for e in entities.values()
        if e.canonical == "caliper_slides_free"
    )
    caliper_part = next(
        e.entity_id for e in entities.values() if e.canonical == "brake_caliper"
    )
    assert any(
        r.subject_entity_id == caliper_free
        and r.object_entity_id == caliper_part
        and r.predicate.value == "affects"
        for r in diag_rels
    )


_SPURIOUS_SYMPTOM_CANONICALS = frozenset(
    {"customer", "low_speed", "the_sound", "28_000_miles", "the_front_wheels", "squealing_noise"}
)


@pytest.mark.skipif(not spacy_available(), reason="spaCy model not installed")
def test_spacy_heuristics_do_not_pollute_comparison_or_diagnosis_rels(monkeypatch):
    """CLM-0009 regression: confirmed tier excludes spaCy noun-chunk noise."""
    from app.core.config import Settings
    import app.modules.nlp.entity_extractor as entity_extractor

    enabled = Settings(NLP_ENABLE_SPACY=True)
    monkeypatch.setattr(entity_extractor, "get_settings", lambda: enabled)
    entity_extractor._SPACY_NLP = None  # noqa: SLF001

    result = NLPPipeline().analyze(_braking_claim())

    assert any(
        e.extraction_method == ExtractionMethod.SPACY_HEURISTIC
        for ext in result.field_extractions
        for e in ext.entities
    )

    for pair in result.complaint_diagnosis_comparison.related_pairs:
        assert pair.symptom_canonical not in _SPURIOUS_SYMPTOM_CANONICALS

    entities = {
        e.entity_id: e for ext in result.field_extractions for e in ext.entities
    }
    for rel in result.entity_relationships:
        if rel.source_field != TextSourceField.TECHNICIAN_DIAGNOSIS:
            continue
        obj = entities.get(rel.object_entity_id)
        assert obj is not None
        assert is_confirmed_entity(obj)

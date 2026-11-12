import json

from app.modules.nlp.llm_contextual_provider import _llm_payload_usable
from app.modules.nlp.llm_nlp_normalize import normalize_llm_nlp_payload
from app.modules.nlp.llm_nlp_schemas import LLMNlpExtractionResponse
from app.modules.nlp.llm_nlp_validator import validate_llm_nlp_response
from app.modules.nlp.schemas import TextSourceField


def test_coerces_invalid_category_and_certainty():
    raw = {
        "entities": [
            {
                "temp_id": "L1",
                "text": "highway",
                "canonical": "highway_driving",
                "category": "condition",
                "source_field": "customer_complaint",
                "source_excerpt": "highway",
            },
            {
                "temp_id": "L2",
                "text": "flush",
                "canonical": "flush",
                "category": "action",
                "source_field": "recommended_repair",
                "source_excerpt": "flush",
            },
        ],
        "relationships": [
            {
                "subject_temp_id": "L1",
                "object_temp_id": "L2",
                "predicate": "affects",
                "source_field": "customer_complaint",
                "source_excerpt": "highway",
                "certainty": "conditional",
            }
        ],
        "observations": [],
    }
    norm, notes = normalize_llm_nlp_payload(raw)
    assert norm["entities"][0]["category"] == "operating_condition"
    assert norm["entities"][1]["category"] == "repair_action"
    assert norm["relationships"][0]["certainty"] == "reported"
    assert not notes or all("dropped" not in n for n in notes)


def test_rejects_truncated_empty_payload():
    parsed = LLMNlpExtractionResponse.model_validate(
        {"entities": [], "relationships": [], "observations": []}
    )
    assert not _llm_payload_usable(parsed, raw="{}", finish_reason="length")


def test_validate_accepts_coerced_payload():
    payload = {
        "entities": [
            {
                "temp_id": "L1",
                "text": "visual inspection",
                "canonical": "visual_inspection",
                "category": "diagnostic_method",
                "source_field": "technician_diagnosis",
                "source_excerpt": "visual inspection",
            }
        ],
        "relationships": [],
        "observations": [],
    }
    originals = {TextSourceField.TECHNICIAN_DIAGNOSIS: "Performed visual inspection of pads."}
    parsed, errors = validate_llm_nlp_response(json.dumps(payload), originals=originals)
    assert parsed is not None
    assert parsed.entities[0].category.value == "diagnostic"
    assert not any(e.startswith("schema:") for e in errors)

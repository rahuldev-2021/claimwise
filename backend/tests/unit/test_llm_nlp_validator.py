import json

from app.modules.nlp.llm_nlp_validator import validate_llm_nlp_response
from app.modules.nlp.schemas import TextSourceField


def test_rejects_hallucinated_dtc():
    raw = json.dumps(
        {
            "entities": [
                {
                    "temp_id": "L1",
                    "text": "P9999",
                    "canonical": "P9999",
                    "category": "dtc_code",
                    "source_field": "technician_diagnosis",
                    "source_excerpt": "P9999",
                }
            ],
            "relationships": [],
            "observations": [],
        }
    )
    originals = {TextSourceField.TECHNICIAN_DIAGNOSIS: "No codes found."}
    parsed, errors = validate_llm_nlp_response(raw, originals=originals)
    assert parsed is None
    assert any("ungrounded" in e or "invented" in e for e in errors)

from app.modules.nlp.entity_extractor import extract_entities
from app.modules.nlp.schemas import EntityCategory, TextSourceField


def test_extracts_engine_and_rattle():
    text = "Engine rattling noise during cold start"
    entities, modes = extract_entities(text, TextSourceField.CUSTOMER_COMPLAINT)
    assert "rules" in modes
    canonicals = {e.canonical for e in entities}
    assert "engine" in canonicals
    assert "abnormal_noise" in canonicals


def test_negation_detected():
    text = "No abnormal noise at idle"
    entities, _ = extract_entities(text, TextSourceField.CUSTOMER_COMPLAINT)
    noise_entities = [e for e in entities if e.canonical == "abnormal_noise"]
    assert noise_entities
    assert noise_entities[0].negated is True


def test_dtc_extraction():
    text = "Stored fault code P0401 insufficient flow"
    entities, _ = extract_entities(text, TextSourceField.TECHNICIAN_DIAGNOSIS)
    assert any("p0401" in e.text.lower() for e in entities)


def test_voltage_measurement():
    text = "Alternator output measured at 11.2V under load"
    entities, _ = extract_entities(text, TextSourceField.TECHNICIAN_DIAGNOSIS)
    assert any(e.category == EntityCategory.MEASUREMENT for e in entities)


def test_fuzzy_transmission_noise():
    text = "transmision noise when shifting"
    entities, modes = extract_entities(text, TextSourceField.CUSTOMER_COMPLAINT)
    assert "fuzzy" in modes
    canonicals = {e.canonical for e in entities}
    assert "transmission" in canonicals

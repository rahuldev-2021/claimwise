from app.modules.nlp.entity_extractor import extract_entities
from app.modules.nlp.schemas import EntityCategory, TextSourceField


def test_celsius_with_degree_symbol():
    text = "engine temperature reached 110°c"
    entities, _ = extract_entities(text, TextSourceField.TECHNICIAN_DIAGNOSIS)
    temps = [e for e in entities if e.canonical.startswith("temperature_")]
    assert any("110" in e.canonical and "C" in e.canonical.upper() for e in temps)


def test_celsius_with_space():
    text = "coolant temperature is 105 c"
    entities, _ = extract_entities(text, TextSourceField.TECHNICIAN_DIAGNOSIS)
    assert any(e.canonical == "temperature_105_C" for e in entities)


def test_fahrenheit():
    text = "temperature reached 230 f"
    entities, _ = extract_entities(text, TextSourceField.TECHNICIAN_DIAGNOSIS)
    assert any(e.canonical == "temperature_230_F" for e in entities)


def test_voltage_still_extracted():
    text = "alternator output measured at 11.2v under load"
    entities, _ = extract_entities(text, TextSourceField.TECHNICIAN_DIAGNOSIS)
    assert any(e.category == EntityCategory.MEASUREMENT and "voltage" in e.canonical for e in entities)

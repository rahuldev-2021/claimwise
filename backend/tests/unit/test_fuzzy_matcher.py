from app.modules.nlp.entity_extractor import extract_entities
from app.modules.nlp.fuzzy_matcher import find_fuzzy_matches
from app.modules.nlp.schemas import MatchMethod, TextSourceField


def test_fuzzy_matches_misspelled_engine_noise():
    text = "engin ratling while accelerating"
    matches = find_fuzzy_matches(text, set(), threshold=0.8)
    canonicals = {m.canonical for m in matches}
    assert "engine" in canonicals
    assert "abnormal_noise" in canonicals


def test_fuzzy_brake_pad():
    text = "customer reports brak pad squeal"
    entities, modes = extract_entities(text, TextSourceField.CUSTOMER_COMPLAINT)
    assert "fuzzy" in modes
    assert any(e.canonical == "brake_pad" for e in entities)


def test_fuzzy_unknown_term_no_match():
    text = "garden hose attachment broken"
    entities, modes = extract_entities(text, TextSourceField.CUSTOMER_COMPLAINT)
    automotive = {e.canonical for e in entities if e.match_method == MatchMethod.FUZZY}
    assert "garden" not in automotive
    assert "hose" not in automotive


def test_exact_match_priority_over_fuzzy():
    text = "engine rattling noise"
    entities, _ = extract_entities(text, TextSourceField.CUSTOMER_COMPLAINT)
    engine = next(e for e in entities if e.canonical == "engine")
    assert engine.match_method == MatchMethod.ALIAS

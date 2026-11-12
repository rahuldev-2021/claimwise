import pytest

from app.core.config import get_settings
from app.modules.nlp.entity_extractor import extract_entities, spacy_available
from app.modules.nlp.schemas import TextSourceField


def test_pipeline_modes_without_spacy_do_not_claim_spacy():
    entities, modes = extract_entities("engine noise", TextSourceField.CUSTOMER_COMPLAINT)
    assert entities
    if not spacy_available():
        assert "spacy" not in modes


@pytest.mark.skipif(not spacy_available(), reason="spaCy model not installed")
def test_spacy_mode_when_available():
    _, modes = extract_entities("engine rattling on cold start", TextSourceField.CUSTOMER_COMPLAINT)
    assert "spacy" in modes


def test_nlp_still_extracts_when_spacy_disabled(monkeypatch):
    from app.core.config import Settings
    import app.modules.nlp.entity_extractor as entity_extractor

    disabled = Settings(NLP_ENABLE_SPACY=False)
    monkeypatch.setattr(entity_extractor, "get_settings", lambda: disabled)
    entities, modes = extract_entities(
        "squealing when braking",
        TextSourceField.CUSTOMER_COMPLAINT,
    )
    assert entities
    assert "spacy" not in modes
    assert not spacy_available()

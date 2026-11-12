from app.modules.nlp.entity_confidence import is_confirmed_entity
from app.modules.nlp.schemas import EntityCategory, ExtractedEntity, ExtractionMethod, TextSourceField


def _ent(method: ExtractionMethod) -> ExtractedEntity:
    return ExtractedEntity(
        text="x",
        canonical="x",
        category=EntityCategory.SYMPTOM,
        source_field=TextSourceField.CUSTOMER_COMPLAINT,
        extraction_method=method,
    )


def test_taxonomy_regex_fuzzy_rule_based_are_confirmed():
    assert is_confirmed_entity(_ent(ExtractionMethod.TAXONOMY))
    assert is_confirmed_entity(_ent(ExtractionMethod.REGEX))
    assert is_confirmed_entity(_ent(ExtractionMethod.RULE_BASED))
    assert is_confirmed_entity(_ent(ExtractionMethod.FUZZY))


def test_spacy_heuristic_not_confirmed():
    assert not is_confirmed_entity(_ent(ExtractionMethod.SPACY_HEURISTIC))

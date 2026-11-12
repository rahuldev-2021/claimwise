"""Confirmed vs heuristic entity tiers for downstream NLP consumers."""

from app.modules.nlp.schemas import ExtractedEntity, ExtractionMethod

CONFIRMED_EXTRACTION_METHODS: frozenset[ExtractionMethod] = frozenset(
    {
        ExtractionMethod.TAXONOMY,
        ExtractionMethod.REGEX,
        ExtractionMethod.RULE_BASED,
        ExtractionMethod.FUZZY,
    }
)

HEURISTIC_EXTRACTION_METHODS: frozenset[ExtractionMethod] = frozenset(
    {
        ExtractionMethod.SPACY_HEURISTIC,
    }
)


def is_confirmed_entity(entity: ExtractedEntity) -> bool:
    """Entities that may drive comparison, TV hints, and LLM fallback signals."""
    if entity.extraction_method == ExtractionMethod.LLM:
        return bool(getattr(entity, "llm_reconciled", False))
    if entity.extraction_method in HEURISTIC_EXTRACTION_METHODS:
        return False
    return entity.extraction_method in CONFIRMED_EXTRACTION_METHODS


def confirmed_entities(entities: list[ExtractedEntity]) -> list[ExtractedEntity]:
    return [e for e in entities if is_confirmed_entity(e)]

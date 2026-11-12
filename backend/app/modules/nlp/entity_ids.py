"""Assign stable entity IDs within one NLP analysis run."""

from app.modules.nlp.schemas import FieldExtraction


def assign_entity_ids(field_extractions: list[FieldExtraction]) -> None:
    counter = 1
    for ext in field_extractions:
        for ent in ext.entities:
            ent.entity_id = f"ENT-{counter:03d}"
            counter += 1

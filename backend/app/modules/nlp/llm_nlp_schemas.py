"""Structured contracts for optional LLM NLP fallback."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.nlp.schemas import (
    EntityCategory,
    RelationshipCertainty,
    RelationshipPolarity,
    RelationshipPredicate,
    TextSourceField,
)


class LLMNlpEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temp_id: str
    text: str
    canonical: str
    category: EntityCategory
    source_field: TextSourceField
    source_excerpt: str
    span_start: Optional[int] = None
    span_end: Optional[int] = None
    negated: bool = False
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    source_certainty: Optional[RelationshipCertainty] = None


class LLMNlpRelationship(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_temp_id: str
    object_temp_id: str
    predicate: RelationshipPredicate
    source_field: TextSourceField
    source_excerpt: str
    polarity: RelationshipPolarity = RelationshipPolarity.POSITIVE
    certainty: RelationshipCertainty = RelationshipCertainty.REPORTED
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class LLMNlpObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str


class LLMNlpExtractionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entities: list[LLMNlpEntity] = Field(default_factory=list)
    relationships: list[LLMNlpRelationship] = Field(default_factory=list)
    observations: list[LLMNlpObservation] = Field(default_factory=list)

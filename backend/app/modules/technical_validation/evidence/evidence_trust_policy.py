"""Multi-dimensional evidence trust (dimensions are not collapsed for rule decisions)."""

from __future__ import annotations

from dataclasses import dataclass

from app.modules.rag.schemas import RetrievedPassage
from app.modules.technical_validation.schemas import EvidenceSupportClass
from app.schemas.claim import ClaimInput


@dataclass(frozen=True)
class EvidenceTrustDimensions:
    source_verification: str
    source_origin: str
    evidence_scope: str
    vehicle_applicable: bool
    repair_applicable: bool
    directness: EvidenceSupportClass
    retrieval_relevance: float
    contradictory: bool
    trust_summary: str


def assess_passage_trust(
    passage: RetrievedPassage,
    claim: ClaimInput,
    *,
    support_class: EvidenceSupportClass,
    vehicle_applicable: bool,
    contradictory: bool = False,
) -> EvidenceTrustDimensions:
    verification = passage.verification_status or "UNVERIFIED"
    origin = passage.evidence_source_type or str(
        passage.metadata.get("evidence_source_type", "")
    )
    scope = passage.evidence_scope or str(passage.metadata.get("evidence_scope", ""))
    repair_applicable = _repair_applicable(passage, claim)

    parts = []
    if verification != "VERIFIED":
        parts.append(f"verification={verification}")
    if not vehicle_applicable:
        parts.append("vehicle mismatch")
    if not repair_applicable:
        parts.append("repair category may not match")
    if origin == "CLAIM_UPLOAD" and verification != "VERIFIED":
        parts.append("claim upload not verified")
    if contradictory:
        parts.append("marked contradictory")
    summary = "; ".join(parts) if parts else "standard trust review"

    return EvidenceTrustDimensions(
        source_verification=verification,
        source_origin=origin or "UNKNOWN",
        evidence_scope=scope,
        vehicle_applicable=vehicle_applicable,
        repair_applicable=repair_applicable,
        directness=support_class,
        retrieval_relevance=float(passage.score),
        contradictory=contradictory,
        trust_summary=summary,
    )


def display_quality_score(dimensions: EvidenceTrustDimensions) -> float:
    """Derived summary for UI only — rules must use dimensions, not this alone."""
    score = 0.4
    if dimensions.directness == EvidenceSupportClass.DIRECT_SUPPORT:
        score = 0.72
    elif dimensions.directness == EvidenceSupportClass.INDIRECT_SUPPORT:
        score = 0.52
    if dimensions.source_verification == "VERIFIED":
        score = min(1.0, score + 0.08)
    elif dimensions.source_verification == "PENDING":
        score = max(0.05, score - 0.22)
    elif dimensions.source_verification == "UNVERIFIED":
        score = max(0.1, score - 0.12)
    if dimensions.source_origin == "CLAIM_UPLOAD" and dimensions.source_verification != "VERIFIED":
        score = min(score, 0.55)
    if not dimensions.vehicle_applicable:
        score = max(0.1, score - 0.15)
    if dimensions.contradictory:
        score = max(0.05, score - 0.25)
    return round(score, 3)


def _repair_applicable(passage: RetrievedPassage, claim: ClaimInput) -> bool:
    cat = str(passage.metadata.get("repair_category", "")).upper()
    claim_cat = (claim.recommended_repair.repair_category or "").upper()
    if not cat or not claim_cat:
        return True
    return cat == claim_cat

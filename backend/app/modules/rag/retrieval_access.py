"""Tenant and claim isolation for retrieved chunks."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalAccessContext:
    """Trust boundary: set only from persisted claim + authenticated org."""

    org_id: str
    claim_id: str


def chunk_visible_to_requester(
    metadata: dict[str, object],
    access: RetrievalAccessContext | None,
) -> bool:
    """Fail closed: unknown or invalid scope is never returned."""
    if not metadata:
        return False

    scope = str(metadata.get("evidence_scope", "")).strip().lower()
    if scope == "global":
        claim_on_chunk = metadata.get("claim_id")
        if claim_on_chunk not in (None, ""):
            return False
        return True

    if scope == "claim":
        if access is None:
            return False
        chunk_org = str(metadata.get("org_id", "")).strip()
        chunk_claim = str(metadata.get("claim_id", "")).strip()
        if not chunk_org or not chunk_claim:
            return False
        return chunk_org == access.org_id and chunk_claim == access.claim_id

    return False


def filter_hits_by_scope(hits: list, access: RetrievalAccessContext | None) -> list:
    """Drop hits that fail scope rules."""
    kept: list = []
    for hit in hits:
        meta = getattr(hit, "metadata", None) or {}
        if chunk_visible_to_requester(dict(meta), access):
            kept.append(hit)
    return kept

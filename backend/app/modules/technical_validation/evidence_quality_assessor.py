"""Summarize evidence quality (separate from retrieval relevance)."""

from app.modules.technical_validation.schemas import ClassifiedEvidence, EvidenceSupportClass


def summarize_quality(classified: list[ClassifiedEvidence]) -> str:
    if not classified:
        return "No retrieved passages to assess."

    direct = sum(1 for c in classified if c.support_class == EvidenceSupportClass.DIRECT_SUPPORT)
    verified = sum(1 for c in classified if c.verification_status == "VERIFIED")
    avg_quality = sum(c.quality_score for c in classified) / len(classified)

    parts = [
        f"{len(classified)} passage(s) reviewed.",
        f"{direct} direct-support passage(s).",
        f"{verified} verified source(s).",
        f"Mean evidence quality score {avg_quality:.2f} (not a retrieval score).",
    ]
    return " ".join(parts)

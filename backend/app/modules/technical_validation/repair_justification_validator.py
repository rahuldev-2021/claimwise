"""Assess whether recommended repair aligns with diagnosis scope."""

import re

from app.modules.nlp.schemas import NLPAnalysisResult
from app.modules.nlp.taxonomy_data import HEAVY_REPAIR_TERMS, LIGHT_REPAIR_TERMS
from app.modules.technical_validation.schemas import ClassifiedEvidence, RepairJustificationAssessment
from app.schemas.claim import ClaimInput
from app.schemas.technical_validation import RepairActionAssessment, RepairJustificationStatus


def assess_repair_justification(
    claim: ClaimInput,
    nlp: NLPAnalysisResult,
) -> RepairJustificationAssessment:
    repair_blob = (
        f"{claim.recommended_repair.recommended_action} "
        f"{claim.recommended_repair.part_description} "
        f"{claim.recommended_repair.repair_category}"
    ).lower()
    diagnosis_blob = claim.technician_diagnosis.lower()
    structured = nlp.structured_extraction

    heavy_recommended = any(t in repair_blob for t in HEAVY_REPAIR_TERMS)
    light_diagnosis = any(t in diagnosis_blob for t in LIGHT_REPAIR_TERMS)

    mismatch = heavy_recommended and light_diagnosis

    repair_action = structured.repair_action or claim.recommended_repair.recommended_action
    part = claim.recommended_repair.part_description
    component = structured.component

    if mismatch:
        summary = (
            "Recommended repair appears more extensive than diagnosis wording suggests "
            "(e.g. major assembly vs lighter diagnostic focus)."
        )
    elif component:
        summary = (
            f"Recommended {repair_action or 'repair'} on {part} relates to "
            f"component context '{component.replace('_', ' ')}'."
        )
    else:
        summary = f"Recommended action: {repair_action or part}. Verify alignment with diagnosis."

    return RepairJustificationAssessment(summary=summary, heavy_vs_light_mismatch=mismatch)


def _split_repair_operations(text: str) -> list[str]:
    parts = re.split(r"\s+and\s+|,\s*|;\s*", text, flags=re.IGNORECASE)
    return [p.strip() for p in parts if p.strip()]


def _finding_in_text(blob: str, needles: tuple[str, ...]) -> list[str]:
    found: list[str] = []
    lower = blob.lower()
    for n in needles:
        if n in lower:
            found.append(n)
    return found


def assess_repair_actions(
    claim: ClaimInput,
    nlp: NLPAnalysisResult,
    classified: list[ClassifiedEvidence],
) -> list[RepairActionAssessment]:
    action_text = (
        claim.recommended_repair.recommended_action
        or claim.recommended_repair.part_description
        or ""
    )
    operations = _split_repair_operations(action_text) or [action_text.strip() or "recommended repair"]
    diagnosis = claim.technician_diagnosis.lower()
    structured = nlp.structured_extraction
    component = (structured.component or "").replace("_", " ")

    assessments: list[RepairActionAssessment] = []
    for op in operations:
        op_lower = op.lower()
        linked: list[str] = []
        status = RepairJustificationStatus.INSUFFICIENT_INFORMATION
        explanation = "Unable to link this operation to a specific diagnostic finding."
        supporting_ids: list[str] = []
        contradictory_ids: list[str] = []

        if "brake pad" in op_lower or "pad" in op_lower:
            if any(k in diagnosis for k in ("pad", "thickness", "worn", "minimum")):
                linked = [f for f in ("brake pad wear", "pad thickness") if f.split()[0] in diagnosis]
                status = RepairJustificationStatus.JUSTIFIED
                explanation = "Operation aligns with pad-related findings in submitted diagnosis."
            else:
                status = RepairJustificationStatus.NOT_SUFFICIENTLY_JUSTIFIED
                explanation = "Pad replacement not clearly linked to pad measurements in diagnosis."

        elif "rotor" in op_lower or "resurface" in op_lower:
            if any(k in diagnosis for k in ("rotor", "heat spot", "scoring", "warp")):
                linked = [f for f in ("rotor heat spot", "rotor scoring") if "rotor" in diagnosis]
                status = RepairJustificationStatus.PARTIALLY_JUSTIFIED
                explanation = "Rotor operation linked to rotor-related diagnosis wording."
            else:
                status = RepairJustificationStatus.NOT_SUFFICIENTLY_JUSTIFIED
                explanation = (
                    "Rotor work is not clearly supported by rotor-specific findings in diagnosis."
                )

        for ev in classified:
            ev_blob = f"{ev.excerpt} {ev.document_type}".lower()
            if op_lower[:12] and op_lower[:12] in ev_blob:
                if ev.support_class.value == "CONTRADICTORY":
                    contradictory_ids.append(ev.chunk_id)
                elif ev.support_class.value in ("DIRECT_SUPPORT", "INDIRECT_SUPPORT"):
                    supporting_ids.append(ev.chunk_id)
                    if status == RepairJustificationStatus.INSUFFICIENT_INFORMATION:
                        status = RepairJustificationStatus.PARTIALLY_JUSTIFIED
                        explanation = "Retrieved evidence partially supports this operation."

        assessments.append(
            RepairActionAssessment(
                original_text=op,
                normalized_operation=op.lower(),
                component=component or None,
                associated_diagnostic_findings=linked,
                supporting_evidence_ids=supporting_ids,
                contradictory_evidence_ids=contradictory_ids,
                justification_status=status,
                explanation=explanation,
            )
        )
    return assessments

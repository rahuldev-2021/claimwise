"""Build narrative text for recommended repair without duplicating description and action."""

from app.schemas.repair import Repair


def repair_narrative_text(repair: Repair) -> str:
    category = (repair.repair_category or "").strip()
    desc = repair.part_description.strip()
    action = repair.recommended_action.strip()
    part_no = (repair.part_number or "").strip()

    if action and desc and action.casefold() == desc.casefold():
        body = desc
    elif desc and action:
        body = f"{desc}. {action}" if desc not in action and action not in desc else action
    else:
        body = desc or action

    # Category is structured metadata on Repair — omit from NLP narrative so spans
    # align with submitted description/action text (not RO category labels).
    return " ".join(p for p in (body, part_no) if p)

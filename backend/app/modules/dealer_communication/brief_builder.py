"""Build dealer communication hints from existing assessment outputs."""

from decimal import Decimal
from pathlib import Path

from app.core.config import Settings
from app.modules.financial_validation.config.loader import load_financial_config
from app.schemas.claim import ClaimInput
from app.schemas.dealer_communication import (
    BenchmarkPosition,
    ClaimResponseVerdict,
    DealerClaimResponse,
    DealerCommunicationBrief,
    FinancialDimensionBrief,
)
from app.schemas.financial_validation import FinancialStatus, FinancialValidationResult
from app.schemas.technical_validation import TechnicalStatus, TechnicalValidationResult


def _position_from_pct(
    pct: Decimal | None,
    *,
    within_min: Decimal,
    within_max: Decimal,
) -> BenchmarkPosition:
    if pct is None:
        return BenchmarkPosition.UNKNOWN
    if pct < within_min:
        return BenchmarkPosition.BELOW_TYPICAL
    if pct > within_max:
        return BenchmarkPosition.ABOVE_TYPICAL
    return BenchmarkPosition.NEAR_TYPICAL


def _combine_positions(a: BenchmarkPosition, b: BenchmarkPosition) -> BenchmarkPosition:
    order = {
        BenchmarkPosition.UNKNOWN: 0,
        BenchmarkPosition.NEAR_TYPICAL: 1,
        BenchmarkPosition.BELOW_TYPICAL: 2,
        BenchmarkPosition.ABOVE_TYPICAL: 3,
    }
    return a if order[a] >= order[b] else b


def _fmt_money(amount: Decimal, currency: str) -> str:
    return f"{amount:.2f} {currency.upper()}"


def _technical_dealer_note(tv: TechnicalValidationResult) -> str:
    status = tv.technical_status
    if status == TechnicalStatus.SUPPORTED:
        return (
            "Technical review supports the repair narrative. Focus customer communication on "
            "what was found and what was fixed; claim approval still requires human review."
        )
    if status == TechnicalStatus.QUESTIONABLE:
        return (
            "Some repair lines need clearer justification. Explain each operation to the customer "
            "and gather any missing evidence before resubmitting the claim."
        )
    if status == TechnicalStatus.NEEDS_REVIEW:
        return (
            "Technical flags need reviewer attention. Avoid promising outcomes; explain that "
            "additional documentation or diagnosis may be requested."
        )
    if status == TechnicalStatus.INSUFFICIENT_EVIDENCE:
        return (
            "Evidence gaps were identified. Tell the customer which documents or test results "
            "are still needed before the claim can move forward."
        )
    return "Technical validation completed; follow the status above when speaking with the customer."


def _dimension_note(
    *,
    label: str,
    position: BenchmarkPosition,
    submitted: Decimal,
    typical: Decimal | None,
    unit: str,
    currency: str,
) -> str:
    if typical is None:
        return f"{label}: no typical benchmark available for comparison."
    sub_s = (
        f"{submitted:.2f} {unit}"
        if unit != currency
        else _fmt_money(submitted, currency)
    )
    typ_s = (
        f"{typical:.2f} {unit}" if unit != currency else _fmt_money(typical, currency)
    )
    if position == BenchmarkPosition.NEAR_TYPICAL:
        return (
            f"{label}: submitted {sub_s} is close to the typical benchmark {typ_s} "
            f"for similar repairs — extra price justification is usually not needed."
        )
    if position == BenchmarkPosition.BELOW_TYPICAL:
        return (
            f"{label}: submitted {sub_s} is below the typical benchmark {typ_s}. "
            f"Confirm the scope is complete and nothing was omitted."
        )
    if position == BenchmarkPosition.ABOVE_TYPICAL:
        return (
            f"{label}: submitted {sub_s} is above the typical benchmark {typ_s}. "
            f"Be ready to explain parts choice, labour steps, and any add-on work."
        )
    return f"{label}: submitted {sub_s}; typical benchmark {typ_s}."


def _pct_phrase(pct: Decimal | None, *, label: str) -> str | None:
    if pct is None:
        return None
    if pct > Decimal("2"):
        return f"{label} is {pct:.1f}% higher than typical"
    if pct < Decimal("-2"):
        return f"{label} is {abs(pct):.1f}% lower than typical"
    return f"{label} is close to typical"


def _build_claim_response(
    *,
    technical: TechnicalValidationResult,
    financial: FinancialValidationResult | None,
    parts_pos: BenchmarkPosition,
    labour_pos: BenchmarkPosition,
    overall: BenchmarkPosition,
) -> DealerClaimResponse:
    because: list[str] = []
    tv = technical.technical_status

    if tv == TechnicalStatus.SUPPORTED:
        because.append("The claim is correct and ready to be approved.")
    elif tv == TechnicalStatus.QUESTIONABLE:
        because.append("Some repair lines need clearer justification.")
    elif tv == TechnicalStatus.INSUFFICIENT_EVIDENCE:
        because.append("Key photos, tests, or documents are still missing.")
    elif tv == TechnicalStatus.NEEDS_REVIEW:
        because.append("Technical checks flagged items for a reviewer.")

    if financial is not None:
        parts_line = _pct_phrase(financial.parts_discrepancy_pct, label="Parts cost")
        labour_line = _pct_phrase(
            financial.labour_discrepancy_pct, label="Labour hours"
        )
        if parts_line:
            because.append(parts_line)
        if labour_line:
            because.append(labour_line)
    elif financial is None:
        because.append("cost comparison was not run on this check")

    verdict = ClaimResponseVerdict.NOT_FULLY_CHECKED
    verdict_label = "Not fully checked"
    summary = ""
    what_to_say = ""

    if tv == TechnicalStatus.INSUFFICIENT_EVIDENCE:
        verdict = ClaimResponseVerdict.NEEDS_DOCUMENTS
        verdict_label = "Needs more documents"
        summary = "The submitted claim is not ready to finalize because required evidence is missing."
        what_to_say = (
            "Tell the customer we still need supporting documents or test results before "
            "the claim can move forward. Send what's listed in the claim and re-run the check."
        )
    elif tv in (TechnicalStatus.NEEDS_REVIEW, TechnicalStatus.QUESTIONABLE):
        verdict = ClaimResponseVerdict.NEEDS_REVIEW
        verdict_label = "Needs review"
        summary = "The submitted claim needs a closer look before anyone can call it complete."
        what_to_say = (
            "Do not promise approval. Explain that a reviewer will look at the repair details "
            "and may ask for more information."
        )
    elif overall == BenchmarkPosition.ABOVE_TYPICAL or (
        financial
        and financial.financial_status == FinancialStatus.OUTSIDE_EXPECTED_RANGE
    ):
        verdict = ClaimResponseVerdict.EXPLAIN_COSTS
        verdict_label = "Explain the costs"
        summary = "The submitted claim looks structurally okay but the costs are above what we usually see."
        what_to_say = (
            "what was replaced, why, and how long the work took. "
            "Have invoices or line items ready if asked."
        )
    elif tv == TechnicalStatus.SUPPORTED and overall in (
        BenchmarkPosition.NEAR_TYPICAL,
        BenchmarkPosition.UNKNOWN,
    ):
        if (
            financial
            and financial.financial_status == FinancialStatus.WITHIN_EXPECTED_RANGE
        ):
            verdict = ClaimResponseVerdict.IN_LINE
            verdict_label = "In line"
            summary = "The submitted claim looks in line — repair story and amounts are reasonable for this type of job."
            what_to_say = (
                "You can tell the dealer/customer the claim fits what we usually see for this repair. "
                "A reviewer still makes the final decision."
            )
        elif financial is None:
            verdict = ClaimResponseVerdict.NOT_FULLY_CHECKED
            verdict_label = "Repair OK — run cost check"
            summary = "The repair story looks supported, but costs were not compared on this run."
            what_to_say = (
                "Repair side looks fine. Run the claim check with cost comparison enabled "
                "before discussing costs with the customer."
            )
        else:
            verdict = ClaimResponseVerdict.NEEDS_REVIEW
            verdict_label = "Needs review"
            summary = "The submitted claim is partly aligned but still needs review."
            what_to_say = "Share the repair details clearly and wait for reviewer guidance before promising an outcome."
    elif overall == BenchmarkPosition.BELOW_TYPICAL:
        verdict = ClaimResponseVerdict.NEEDS_REVIEW
        verdict_label = "Confirm scope"
        summary = "The submitted claim may be below typical amounts — confirm nothing was left out of the scope."
        what_to_say = (
            "Ask whether every step of the repair is on the claim. Lower-than-typical amounts "
            "sometimes mean missing line items."
        )
    else:
        verdict = ClaimResponseVerdict.NEEDS_REVIEW
        verdict_label = "Needs review"
        summary = "The submitted claim needs reviewer input before you give the customer a firm answer."
        what_to_say = "Stay neutral: the claim is in review and you will follow up when there is an update."

    if not summary:
        summary = "The submitted claim was checked — see the cards below for detail."
    elif not summary.endswith("."):
        summary = f"{summary}."

    return DealerClaimResponse(
        verdict=verdict,
        verdict_label=verdict_label,
        summary=summary,
        because=because,
        what_to_say=what_to_say,
    )


def build_dealer_communication_brief(
    claim: ClaimInput,
    financial: FinancialValidationResult | None,
    technical: TechnicalValidationResult,
    *,
    settings: Settings | None = None,
) -> DealerCommunicationBrief:
    """Pure post-processing; does not alter financial status or recommendations."""
    tech_note = _technical_dealer_note(technical)

    within_parts_min = Decimal("-25")
    within_parts_max = Decimal("25")
    within_labour_min = Decimal("-20")
    within_labour_max = Decimal("20")
    if settings is not None:
        config_dir = Path(settings.FINANCIAL_CONFIG_DIR)
        rules = load_financial_config(config_dir).rules
        pb = rules.discrepancy_bands.get("parts_cost_pct") or {}
        lb = rules.discrepancy_bands.get("labour_hours_pct") or {}
        within_parts_min = Decimal(str(pb.get("within_min", -25)))
        within_parts_max = Decimal(str(pb.get("within_max", 25)))
        within_labour_min = Decimal(str(lb.get("within_min", -20)))
        within_labour_max = Decimal(str(lb.get("within_max", 20)))

    if financial is None:
        response = _build_claim_response(
            technical=technical,
            financial=None,
            parts_pos=BenchmarkPosition.UNKNOWN,
            labour_pos=BenchmarkPosition.UNKNOWN,
            overall=BenchmarkPosition.UNKNOWN,
        )
        return DealerCommunicationBrief(
            technical_dealer_note=tech_note,
            dealer_headline="Financial benchmark not available for this run.",
            dealer_talking_points=[tech_note],
            response=response,
        )

    parts_pos = _position_from_pct(
        financial.parts_discrepancy_pct,
        within_min=within_parts_min,
        within_max=within_parts_max,
    )
    labour_pos = _position_from_pct(
        financial.labour_discrepancy_pct,
        within_min=within_labour_min,
        within_max=within_labour_max,
    )
    overall = _combine_positions(parts_pos, labour_pos)
    if (
        parts_pos == BenchmarkPosition.UNKNOWN
        and labour_pos == BenchmarkPosition.UNKNOWN
    ):
        overall = BenchmarkPosition.UNKNOWN

    currency = claim.currency or "USD"
    parts_brief: FinancialDimensionBrief | None = None
    labour_brief: FinancialDimensionBrief | None = None

    if financial.submitted_parts_cost is not None:
        parts_brief = FinancialDimensionBrief(
            dimension="parts",
            position=parts_pos,
            submitted_value=financial.submitted_parts_cost,
            typical_value=financial.predicted_parts_cost,
            discrepancy_pct=financial.parts_discrepancy_pct,
            dealer_note=_dimension_note(
                label="Parts cost",
                position=parts_pos,
                submitted=financial.submitted_parts_cost,
                typical=financial.predicted_parts_cost,
                unit=currency,
                currency=currency,
            ),
        )
    if financial.submitted_labour_hours is not None:
        labour_brief = FinancialDimensionBrief(
            dimension="labour",
            position=labour_pos,
            submitted_value=financial.submitted_labour_hours,
            typical_value=financial.predicted_labour_hours,
            discrepancy_pct=financial.labour_discrepancy_pct,
            dealer_note=_dimension_note(
                label="Labour hours",
                position=labour_pos,
                submitted=financial.submitted_labour_hours,
                typical=financial.predicted_labour_hours,
                unit="hrs",
                currency=currency,
            ),
        )

    price_discussion = overall in (
        BenchmarkPosition.ABOVE_TYPICAL,
        BenchmarkPosition.BELOW_TYPICAL,
    )
    if financial.financial_status == FinancialStatus.WITHIN_EXPECTED_RANGE:
        headline = (
            "Costs look close to typical — focus on the repair story with the customer."
        )
    elif financial.financial_status == FinancialStatus.OUTSIDE_EXPECTED_RANGE:
        headline = "Costs look higher or lower than typical — be ready to explain parts and labour."
    elif financial.financial_status in (
        FinancialStatus.INSUFFICIENT_DATA,
        FinancialStatus.NEEDS_REVIEW,
    ):
        headline = (
            "We could not compare all costs — follow the repair check result above."
        )
    else:
        headline = ""

    dealer_points: list[str] = [tech_note]

    customer_points: list[str] = []
    if overall == BenchmarkPosition.NEAR_TYPICAL:
        customer_points.append(
            "Your submitted repair costs are in line with what we usually see for this type of work."
        )
    elif overall == BenchmarkPosition.ABOVE_TYPICAL:
        customer_points.append(
            "Your claim amounts are higher than typical for this repair — we may ask for more detail on parts and labour."
        )
    elif overall == BenchmarkPosition.BELOW_TYPICAL:
        customer_points.append(
            "Your amounts are lower than typical — we may confirm the full repair scope was captured."
        )

    if technical.technical_status == TechnicalStatus.INSUFFICIENT_EVIDENCE:
        customer_points.append(
            "We still need additional documentation or test results before the claim review can continue."
        )

    response = _build_claim_response(
        technical=technical,
        financial=financial,
        parts_pos=parts_pos,
        labour_pos=labour_pos,
        overall=overall,
    )

    return DealerCommunicationBrief(
        overall_financial_position=overall,
        price_discussion_suggested=price_discussion,
        parts=parts_brief,
        labour=labour_brief,
        dealer_headline=headline,
        dealer_talking_points=dealer_points,
        customer_talking_points=customer_points,
        technical_dealer_note=tech_note,
        response=response,
    )

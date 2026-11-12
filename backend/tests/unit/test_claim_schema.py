"""Tests for the ClaimInput schema."""

from decimal import Decimal

import pytest

from app.schemas.claim import ClaimInput, ClaimStatus


def _base() -> dict:
    return {
        "claim_id": "CLM-001",
        "submission_date": "2026-09-15T10:30:00Z",
        "vehicle": {
            "vehicle_id": "VH-001",
            "make": "Ford",
            "model": "Mustang",
            "model_year": 2022,
        },
        "customer_complaint": "Engine rattling noise.",
        "technician_diagnosis": "Timing chain tensioner failure suspected.",
        "recommended_repair": {
            "repair_category": "ENGINE",
            "part_description": "Timing chain kit",
            "recommended_action": "Replace timing chain",
        },
        "submitted_parts_cost": "1800.00",
        "submitted_labour_hours": "20.0",
        "currency": "USD",
    }


def test_valid_claim():
    c = ClaimInput(**_base())
    assert c.claim_id == "CLM-001"
    assert c.submitted_parts_cost == Decimal("1800.00")
    assert c.submitted_labour_hours == Decimal("20.0")
    assert c.claim_status == ClaimStatus.SUBMITTED


def test_negative_parts_cost_rejected():
    data = _base()
    data["submitted_parts_cost"] = "-100"
    with pytest.raises(ValueError):
        ClaimInput(**data)


def test_negative_labour_hours_rejected():
    data = _base()
    data["submitted_labour_hours"] = "-5"
    with pytest.raises(ValueError):
        ClaimInput(**data)


def test_zero_cost_accepted():
    data = _base()
    data["submitted_parts_cost"] = "0"
    c = ClaimInput(**data)
    assert c.submitted_parts_cost == Decimal("0")


def test_invalid_currency_rejected():
    data = _base()
    data["currency"] = "US"
    with pytest.raises(ValueError, match="three-letter uppercase"):
        ClaimInput(**data)


def test_numeric_currency_rejected():
    data = _base()
    data["currency"] = "123"
    with pytest.raises(ValueError, match="three-letter uppercase"):
        ClaimInput(**data)


def test_blank_complaint_rejected():
    data = _base()
    data["customer_complaint"] = "   "
    with pytest.raises(ValueError, match="must not be blank"):
        ClaimInput(**data)


def test_blank_diagnosis_rejected():
    data = _base()
    data["technician_diagnosis"] = ""
    with pytest.raises(ValueError, match="must not be blank"):
        ClaimInput(**data)


def test_naive_datetime_rejected():
    data = _base()
    data["submission_date"] = "2026-09-15T10:30:00"
    with pytest.raises(ValueError, match="timezone-aware"):
        ClaimInput(**data)


def test_invalid_claim_status_rejected():
    data = _base()
    data["claim_status"] = "APPROVED"
    with pytest.raises(ValueError):
        ClaimInput(**data)


def test_extra_fields_rejected():
    data = _base()
    data["priority"] = "high"
    with pytest.raises(ValueError):
        ClaimInput(**data)


def test_decimal_from_float():
    data = _base()
    data["submitted_parts_cost"] = 1800.50
    c = ClaimInput(**data)
    assert c.submitted_parts_cost == Decimal("1800.5")

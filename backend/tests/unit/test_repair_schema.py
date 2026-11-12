"""Tests for the Repair schema."""

import pytest

from app.schemas.repair import Repair


def _base() -> dict:
    return {
        "repair_category": "ENGINE",
        "part_description": "Timing chain kit",
        "recommended_action": "Replace timing chain",
    }


def test_valid_repair():
    r = Repair(**_base())
    assert r.repair_category == "ENGINE"
    assert r.part_number is None


def test_category_normalized_to_uppercase():
    data = _base()
    data["repair_category"] = "  engine  "
    r = Repair(**data)
    assert r.repair_category == "ENGINE"


def test_blank_category_rejected():
    data = _base()
    data["repair_category"] = "   "
    with pytest.raises(ValueError, match="must not be blank"):
        Repair(**data)


def test_blank_recommended_action_rejected():
    data = _base()
    data["recommended_action"] = ""
    with pytest.raises(ValueError, match="must not be blank"):
        Repair(**data)


def test_unknown_category_accepted():
    data = _base()
    data["repair_category"] = "EXHAUST"
    r = Repair(**data)
    assert r.repair_category == "EXHAUST"


def test_extra_fields_rejected():
    data = _base()
    data["severity"] = "high"
    with pytest.raises(ValueError):
        Repair(**data)

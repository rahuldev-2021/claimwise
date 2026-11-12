"""Tests for the Vehicle schema."""

import pytest

from app.schemas.vehicle import Vehicle


def _base() -> dict:
    return {
        "vehicle_id": "VH-001",
        "make": "Ford",
        "model": "Mustang",
        "model_year": 2022,
    }


def test_valid_vehicle():
    v = Vehicle(**_base())
    assert v.vehicle_id == "VH-001"
    assert v.make == "Ford"
    assert v.model_year == 2022


def test_optional_fields_default_to_none():
    v = Vehicle(**_base())
    assert v.vin is None
    assert v.engine_type is None
    assert v.mileage is None


def test_whitespace_stripped():
    data = _base()
    data["make"] = "  Ford  "
    v = Vehicle(**data)
    assert v.make == "Ford"


def test_blank_make_rejected():
    data = _base()
    data["make"] = "   "
    with pytest.raises(ValueError, match="must not be blank"):
        Vehicle(**data)


def test_model_year_too_low():
    data = _base()
    data["model_year"] = 1900
    with pytest.raises(ValueError, match="Model year must be between"):
        Vehicle(**data)


def test_model_year_too_high():
    data = _base()
    data["model_year"] = 2090
    with pytest.raises(ValueError, match="Model year must be between"):
        Vehicle(**data)


def test_negative_mileage_rejected():
    data = _base()
    data["mileage"] = -100
    with pytest.raises(ValueError):
        Vehicle(**data)


def test_zero_mileage_accepted():
    data = _base()
    data["mileage"] = 0
    v = Vehicle(**data)
    assert v.mileage == 0


def test_extra_fields_rejected():
    data = _base()
    data["color"] = "red"
    with pytest.raises(ValueError):
        Vehicle(**data)


def test_blank_vin_becomes_none():
    data = _base()
    data["vin"] = "   "
    v = Vehicle(**data)
    assert v.vin is None

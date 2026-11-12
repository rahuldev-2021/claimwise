"""Lookup synthetic fleet category from make+model (PROVISIONAL)."""

from __future__ import annotations

# Aligns with synthetic_v1 generator labels; default when unknown.
_LOOKUP: dict[tuple[str, str], str] = {
    ("Apex", "Compact"): "HATCHBACK",
    ("Apex", "Sedan"): "SEDAN",
    ("Apex", "Cross"): "CROSSOVER",
    ("Apex", "Trail"): "SUV",
    ("Bravo", "City"): "HATCHBACK",
    ("Bravo", "Executive"): "SEDAN",
    ("Bravo", "Ridge"): "SUV",
    ("Crest", "Tourer"): "SEDAN",
    ("Crest", "Voyager"): "CROSSOVER",
    ("Delta", "Sport"): "SEDAN",
    ("Delta", "Utility"): "SUV",
    ("Echo", "Mini"): "HATCHBACK",
    ("ACME", "Sedan"): "SEDAN",
    ("ACME", "SUV"): "SUV",
    ("BETA", "Coupe"): "SEDAN",
    ("Ford", "F-150"): "TRUCK",
}


def lookup_vehicle_category(make: str, model: str) -> str | None:
    key = (make.strip(), model.strip())
    return _LOOKUP.get(key)

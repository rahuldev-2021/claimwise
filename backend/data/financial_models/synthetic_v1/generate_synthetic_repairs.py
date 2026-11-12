"""
Reproducible synthetic historical repair dataset for CLAIMWISE Phase 6 ML.
SIMULATION ONLY — not OEM pricing or real historical records.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

SCRIPT_VERSION = "1.1.0"
DATASET_VERSION = "synthetic_v1.1"
RANDOM_SEED = 42
TARGET_RECORDS = 10_000
CURRENCY = "USD"

OUTPUT_DIR = Path(__file__).resolve().parent

MAKES_MODELS: list[tuple[str, str, str]] = [
    ("Apex", "Compact", "HATCHBACK"),
    ("Apex", "Sedan", "SEDAN"),
    ("Apex", "Cross", "CROSSOVER"),
    ("Apex", "Trail", "SUV"),
    ("Bravo", "City", "HATCHBACK"),
    ("Bravo", "Executive", "SEDAN"),
    ("Bravo", "Ridge", "SUV"),
    ("Crest", "Tourer", "SEDAN"),
    ("Crest", "Voyager", "CROSSOVER"),
    ("Delta", "Sport", "SEDAN"),
    ("Delta", "Utility", "SUV"),
    ("Echo", "Mini", "HATCHBACK"),
]

ENGINE_TYPES = ["I4", "I4-T", "V6", "V8"]
FUEL_TYPES = ["PETROL", "DIESEL", "HYBRID"]
TRANS_TYPES = ["MANUAL", "AUTOMATIC", "CVT"]

COMPLEXITY = ["LOW", "MEDIUM", "HIGH"]
COMPLEXITY_MULT = {"LOW": 0.85, "MEDIUM": 1.0, "HIGH": 1.35}

CATEGORY_MULT = {
    "HATCHBACK": 0.92,
    "SEDAN": 1.0,
    "CROSSOVER": 1.08,
    "SUV": 1.15,
}


@dataclass(frozen=True)
class RepairTemplate:
    category: str
    component: str
    part: str
    action: str
    base_parts: float
    base_labour: float
    weight: float


REPAIR_TEMPLATES: list[RepairTemplate] = [
    RepairTemplate("BRAKES", "Brake system", "Brake pads", "Replacement", 180, 1.2, 14),
    RepairTemplate("BRAKES", "Brake system", "Brake rotor", "Repair", 320, 1.8, 10),
    RepairTemplate("ENGINE", "Engine assembly", "Timing chain kit", "Replacement", 2100, 9.5, 6),
    RepairTemplate("ENGINE", "Engine cooling", "Water pump", "Replacement", 420, 3.5, 8),
    RepairTemplate("ENGINE", "Engine assembly", "Cylinder head gasket", "Repair", 950, 8.5, 5),
    RepairTemplate("TRANSMISSION", "Transmission system", "Clutch assembly", "Replacement", 1850, 11.0, 5),
    RepairTemplate("TRANSMISSION", "Transmission system", "Shift solenoid", "Replacement", 520, 4.0, 4),
    RepairTemplate("TRANSMISSION", "Transmission system", "Transmission fluid", "Repair", 120, 1.5, 6),
    RepairTemplate("SUSPENSION", "Suspension system", "Shock absorber", "Replacement", 380, 2.5, 9),
    RepairTemplate("SUSPENSION", "Suspension system", "Control arm", "Repair", 290, 2.8, 7),
    RepairTemplate("STEERING", "Steering system", "Steering rack", "Replacement", 1450, 7.5, 4),
    RepairTemplate("STEERING", "Steering system", "Tie rod end", "Repair", 165, 1.5, 8),
    RepairTemplate("ELECTRICAL", "Charging system", "Alternator", "Replacement", 510, 2.8, 9),
    RepairTemplate("ELECTRICAL", "Starting system", "Starter motor", "Repair", 430, 2.2, 7),
    RepairTemplate("COOLING", "Cooling system", "Radiator", "Replacement", 620, 3.2, 8),
    RepairTemplate("COOLING", "Cooling system", "Thermostat", "Repair", 95, 1.1, 6),
    RepairTemplate("FUEL", "Fuel delivery", "Fuel pump", "Replacement", 680, 4.5, 5),
    RepairTemplate("FUEL", "Fuel system", "Fuel injector", "Repair", 240, 2.0, 6),
    RepairTemplate("HVAC", "Climate control", "AC compressor", "Replacement", 980, 5.5, 6),
    RepairTemplate("HVAC", "HVAC system", "Evaporator core", "Repair", 720, 6.0, 4),
    RepairTemplate("BATTERY", "Battery system", "12V battery", "Replacement", 210, 0.6, 10),
    RepairTemplate("BATTERY", "Charging system", "DC-DC converter", "Replacement", 890, 4.2, 3),
    RepairTemplate("EXHAUST", "Exhaust system", "Catalytic converter", "Replacement", 1200, 3.8, 5),
    RepairTemplate("EXHAUST", "Exhaust system", "Muffler", "Repair", 340, 1.6, 7),
    RepairTemplate("BODY", "Body exterior", "Door shell", "Replacement", 780, 5.0, 4),
    RepairTemplate("BODY", "Body exterior", "Bumper cover", "Repair", 450, 3.2, 6),
]

PART_CATALOG: dict[tuple[str, str], str] = {}


def _catalog_part_id(category: str, part: str) -> str:
    key = (category, part)
    if key not in PART_CATALOG:
        slug = part.upper().replace(" ", "-")[:24]
        PART_CATALOG[key] = f"SKU-{category}-{slug}"
    return PART_CATALOG[key]


VALID_TRIPLETS = {(t.category, t.component, t.part) for t in REPAIR_TEMPLATES}

CSV_COLUMNS = [
    "repair_record_id",
    "vehicle_id",
    "vehicle_make",
    "vehicle_model",
    "model_year",
    "vehicle_category",
    "mileage",
    "engine_type",
    "fuel_type",
    "transmission_type",
    "repair_category",
    "component",
    "part",
    "repair_action",
    "repair_complexity",
    "number_of_parts",
    "part_number",
    "currency",
    "parts_cost",
    "labour_hours",
    "price_date",
    "vehicle_age_years",
    "is_synthetic",
    "dataset_version",
]


def _weighted_choice(rng: random.Random, items: list[RepairTemplate]) -> RepairTemplate:
    weights = [t.weight for t in items]
    return rng.choices(items, weights=weights, k=1)[0]


def _synthetic_mileage(rng: random.Random, age_years: int) -> int:
    base = age_years * rng.randint(8000, 14500)
    noise = rng.randint(-6000, 12000)
    return max(500, base + noise)


def _price_date(rng: random.Random, model_year: int) -> date:
    start = date(max(model_year + 1, 2018), 1, 1)
    end = date(2024, 12, 31)
    span = (end - start).days
    if span <= 0:
        return end
    return start + timedelta(days=rng.randint(0, span))


def _financials(
    rng: random.Random,
    tpl: RepairTemplate,
    vehicle_category: str,
    complexity: str,
) -> tuple[float, float]:
    cat_m = CATEGORY_MULT.get(vehicle_category, 1.0)
    cx_m = COMPLEXITY_MULT[complexity]
    parts_noise = math.exp(rng.gauss(0, 0.12))
    labour_noise = math.exp(rng.gauss(0, 0.1))
    supplier = 1.0 + rng.uniform(-0.08, 0.12)
    parts = tpl.base_parts * cat_m * cx_m * parts_noise * supplier
    labour = tpl.base_labour * cx_m * labour_noise * (1.0 + (cat_m - 1.0) * 0.4)
    if tpl.action == "Repair":
        parts *= 0.55
        labour *= 1.15
    parts = round(max(25.0, parts), 2)
    labour = round(max(0.3, labour), 2)
    return parts, labour


def _generate_vehicles(rng: random.Random, n_vehicles: int) -> list[dict]:
    vehicles = []
    for i in range(n_vehicles):
        make, model, category = rng.choice(MAKES_MODELS)
        year = rng.randint(2012, 2023)
        vehicles.append(
            {
                "vehicle_id": f"VH-{i+1:05d}",
                "vehicle_make": make,
                "vehicle_model": model,
                "vehicle_category": category,
                "model_year": year,
                "engine_type": rng.choice(ENGINE_TYPES),
                "fuel_type": rng.choice(FUEL_TYPES),
                "transmission_type": rng.choice(TRANS_TYPES),
            }
        )
    return vehicles


def _generate_records(rng: random.Random, target: int) -> list[dict]:
    n_vehicles = 2800
    vehicles = _generate_vehicles(rng, n_vehicles)
    records: list[dict] = []
    seq = 0
    while len(records) < target:
        veh = rng.choice(vehicles)
        tpl = _weighted_choice(rng, REPAIR_TEMPLATES)
        complexity = rng.choices(COMPLEXITY, weights=[35, 45, 20], k=1)[0]
        pdate = _price_date(rng, veh["model_year"])
        age = pdate.year - veh["model_year"]
        mileage = _synthetic_mileage(rng, age)
        parts, labour = _financials(rng, tpl, veh["vehicle_category"], complexity)
        seq += 1
        part_no = _catalog_part_id(tpl.category, tpl.part)
        records.append(
            {
                "repair_record_id": f"HR-{seq:06d}",
                "vehicle_id": veh["vehicle_id"],
                "vehicle_make": veh["vehicle_make"],
                "vehicle_model": veh["vehicle_model"],
                "model_year": veh["model_year"],
                "vehicle_category": veh["vehicle_category"],
                "mileage": mileage,
                "engine_type": veh["engine_type"],
                "fuel_type": veh["fuel_type"],
                "transmission_type": veh["transmission_type"],
                "repair_category": tpl.category,
                "component": tpl.component,
                "part": tpl.part,
                "repair_action": tpl.action,
                "repair_complexity": complexity,
                "number_of_parts": rng.randint(1, 4 if complexity == "HIGH" else 2),
                "part_number": part_no,
                "currency": CURRENCY,
                "parts_cost": parts,
                "labour_hours": labour,
                "price_date": pdate.isoformat(),
                "vehicle_age_years": age,
                "is_synthetic": "true",
                "dataset_version": DATASET_VERSION,
            }
        )
    return records


def _split_by_vehicle(
    records: list[dict], rng: random.Random
) -> tuple[list[dict], list[dict], list[dict]]:
    by_vehicle: dict[str, list[dict]] = {}
    for r in records:
        by_vehicle.setdefault(r["vehicle_id"], []).append(r)
    vehicle_ids = list(by_vehicle.keys())
    rng.shuffle(vehicle_ids)
    n = len(vehicle_ids)
    n_train = int(n * 0.70)
    n_val = int(n * 0.15)
    train_ids = set(vehicle_ids[:n_train])
    val_ids = set(vehicle_ids[n_train : n_train + n_val])
    test_ids = set(vehicle_ids[n_train + n_val :])

    train, val, test = [], [], []
    for vid, rows in by_vehicle.items():
        if vid in train_ids:
            train.extend(rows)
        elif vid in val_ids:
            val.extend(rows)
        else:
            test.extend(rows)
    return train, val, test


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _edge_cases() -> list[dict]:
    base = {
        "vehicle_make": "Apex",
        "vehicle_model": "Sedan",
        "model_year": 2020,
        "vehicle_category": "SEDAN",
        "engine_type": "I4",
        "fuel_type": "PETROL",
        "transmission_type": "AUTOMATIC",
        "repair_category": "BRAKES",
        "component": "Brake system",
        "part": "Brake pads",
        "repair_action": "Replacement",
        "repair_complexity": "MEDIUM",
        "number_of_parts": 1,
        "part_number": "PN-EDGE-001",
        "currency": CURRENCY,
        "parts_cost": 200.0,
        "labour_hours": 1.5,
        "price_date": "2023-06-01",
        "vehicle_age_years": 3,
        "is_synthetic": "true",
        "dataset_version": DATASET_VERSION,
        "vehicle_id": "VH-EDGE-001",
        "mileage": 40000,
    }
    cases = []
    specs = [
        ("missing_mileage", {"mileage": ""}),
        ("missing_model", {"vehicle_model": ""}),
        ("missing_repair_category", {"repair_category": ""}),
        ("missing_component", {"component": ""}),
        ("unsupported_currency", {"currency": "INR"}),
        ("negative_parts", {"parts_cost": -10}),
        ("negative_labour", {"labour_hours": -1}),
        ("extreme_parts", {"parts_cost": 999999}),
        ("extreme_labour", {"labour_hours": 200}),
        ("unknown_category", {"repair_category": "INVALID_X"}),
        ("duplicate_id", {"repair_record_id": "EDGE-DUP-001"}),
    ]
    for i, (label, patch) in enumerate(specs):
        row = {**base, "repair_record_id": f"EDGE-{i+1:03d}", "edge_case_label": label}
        row.update(patch)
        cases.append(row)
    if cases:
        dup = {**cases[-1]}
        dup["edge_case_label"] = "duplicate_id_second_row"
        cases.append(dup)
    return cases


def _write_charts(train: list[dict], out_dir: Path) -> list[str]:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return ["matplotlib not installed — charts skipped"]

    saved = []
    cats = [r["repair_category"] for r in train]
    parts = [float(r["parts_cost"]) for r in train]
    labour = [float(r["labour_hours"]) for r in train]
    ages = [int(r["vehicle_age_years"]) for r in train]
    miles = [int(r["mileage"]) for r in train]

    fig, ax = plt.subplots(figsize=(10, 4))
    counts = Counter(cats)
    ax.bar(counts.keys(), counts.values())
    ax.set_title("Repair category distribution (train)")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    p = out_dir / "chart_repair_category_distribution.png"
    fig.savefig(p, dpi=120)
    plt.close(fig)
    saved.append(str(p))

    for name, data, fname in [
        ("Parts cost", parts, "chart_parts_cost_distribution.png"),
        ("Labour hours", labour, "chart_labour_hours_distribution.png"),
        ("Vehicle age (years)", ages, "chart_vehicle_age_distribution.png"),
        ("Mileage", miles, "chart_mileage_distribution.png"),
    ]:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(data, bins=40)
        ax.set_title(name)
        fig.tight_layout()
        p = out_dir / fname
        fig.savefig(p, dpi=120)
        plt.close(fig)
        saved.append(str(p))

    by_cat_parts: dict[str, list[float]] = {}
    by_cat_labour: dict[str, list[float]] = {}
    for r in train:
        by_cat_parts.setdefault(r["repair_category"], []).append(float(r["parts_cost"]))
        by_cat_labour.setdefault(r["repair_category"], []).append(float(r["labour_hours"]))

    for title, mapping, fname in [
        ("Median parts cost by category", {k: sum(v) / len(v) for k, v in by_cat_parts.items()}, "chart_parts_cost_by_category.png"),
        ("Median labour hours by category", {k: sum(v) / len(v) for k, v in by_cat_labour.items()}, "chart_labour_hours_by_category.png"),
    ]:
        fig, ax = plt.subplots(figsize=(10, 4))
        keys = sorted(mapping.keys())
        ax.bar(keys, [mapping[k] for k in keys])
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=45)
        fig.tight_layout()
        p = out_dir / fname
        fig.savefig(p, dpi=120)
        plt.close(fig)
        saved.append(str(p))

    return saved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=TARGET_RECORDS)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    parser.add_argument("--out-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    records = _generate_records(rng, args.count)
    train, val, test = _split_by_vehicle(records, random.Random(args.seed + 1))
    edge = _edge_cases()

    out = args.out_dir
    _write_csv(out / "historical_repairs.csv", records)
    _write_csv(out / "train.csv", train)
    _write_csv(out / "validation.csv", val)
    _write_csv(out / "test.csv", test)

    edge_cols = list({k for row in edge for k in row.keys()})
    path_edge = out / "edge_cases.csv"
    with path_edge.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=edge_cols)
        w.writeheader()
        for row in edge:
            w.writerow(row)

    meta = {
        "dataset_version": DATASET_VERSION,
        "generation_script_version": SCRIPT_VERSION,
        "random_seed": args.seed,
        "currency": CURRENCY,
        "synthetic_declaration": "All records are simulated. Not OEM pricing or real warranty history.",
        "total_records": len(records),
        "split_counts": {"train": len(train), "validation": len(val), "test": len(test)},
        "split_strategy": "Group by vehicle_id 70/15/15 — prevents same-vehicle leakage across splits",
        "unique_vehicles": len({r["vehicle_id"] for r in records}),
        "date_range": {
            "min": min(r["price_date"] for r in records),
            "max": max(r["price_date"] for r in records),
        },
    }
    (out / "dataset_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    charts = _write_charts(train, out)
    summary = {
        "record_count": len(records),
        "category_counts": dict(Counter(r["repair_category"] for r in records)),
        "charts": charts,
    }
    (out / "dataset_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

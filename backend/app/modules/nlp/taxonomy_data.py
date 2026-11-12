"""Automotive terminology aliases mapped to canonical snake_case terms."""

from typing import Final

# category -> canonical term -> list of aliases (lowercase)
TAXONOMY_VERSION: Final[str] = "2026.03.1"

TAXONOMY_ALIASES: Final[dict[str, dict[str, list[str]]]] = {
    "component": {
        "engine": ["engine", "motor", "powerplant"],
        "transmission": ["transmission", "gearbox", "trans"],
        "braking_system": ["brake", "brakes", "braking", "brake system"],
        "suspension": ["suspension", "shock", "strut", "stabilizer", "stabiliser"],
        "steering": ["steering", "steering system"],
        "electrical_system": ["electrical", "charging system"],
        "battery": ["battery"],
        "alternator": ["alternator"],
        "cooling_system": ["cooling", "coolant", "radiator"],
        "air_conditioning": ["air conditioning", "a/c", "ac system", "hvac"],
        "timing_chain": ["timing chain", "timing cover", "timing assembly"],
    },
    "part": {
        "brake_pad": [
            "brake pad",
            "brake pads",
            "brake lining",
            "brake linings",
            "front pads",
            "front pad",
        ],
        "brake_rotor": ["brake disc", "brake rotor", "brake rotors", "rotors", "rotor"],
        "brake_caliper": ["brake caliper", "caliper"],
        "spark_plug": ["spark plug", "spark plugs"],
        "oil_filter": ["oil filter"],
        "water_pump": ["water pump"],
        "alternator": ["alternator assembly", "alternator"],
        "engine_block": ["engine block", "block assembly", "complete engine block"],
        "timing_chain_kit": ["timing chain kit", "timing chain", "chain kit"],
        "timing_chain_tensioner": ["timing chain tensioner", "chain tensioner", "tensioner"],
        "blend_door_actuator": ["blend door actuator", "door actuator"],
        "valve_body": ["valve body", "solenoid pack", "transmission valve body"],
        "ac_compressor": ["a/c compressor", "ac compressor", "compressor assembly"],
        "stabilizer_end_link": ["stabilizer bar end link", "end link", "sway bar link"],
        "egr_assembly": ["egr cooler", "egr valve", "egr assembly"],
    },
    "symptom": {
        "abnormal_noise": [
            "rattling",
            "rattle",
            "knocking",
            "knock",
            "squealing",
            "squeal",
            "clunking",
            "clunk",
            "clicking",
            "click",
            "strange noise",
            "unusual sound",
            "abnormal noise",
            "noise",
        ],
        "vibration": ["vibration", "shaking", "shudder"],
        "leakage": ["leak", "leakage", "leaking"],
        "engine_overheating": [
            "overheating",
            "running hot",
            "engine overheating",
            "temperature gauge",
            "red zone",
        ],
        "starting_failure": ["won't start", "starting failure", "no start", "hard start"],
        "reduced_braking": ["pulls when braking", "reduced braking", "brake fade"],
        "poor_ac_cooling": ["warm air", "not cooling", "blows warm", "poor cooling"],
        "shifting_issue": ["hesitates", "jerks", "shifting", "shift quality", "harsh shift"],
        "warning_light": ["warning light", "check engine", "battery warning", "light illuminated"],
        "power_loss": ["loss of power", "lack of power", "reduced power"],
    },
    "diagnostic": {
        "fault_code": ["fault code", "diagnostic code", "trouble code", "dtc"],
        "pressure_test": ["pressure test", "pressure tested"],
        "load_test": ["load test", "under load"],
        "visual_inspection": ["visual inspection", "inspected", "inspection"],
        "measurement": ["measured", "output measured", "thickness measured"],
    },
    "repair_action": {
        "replace": ["replace", "replacement", "replaced"],
        "repair": ["repair", "repaired"],
        "inspect": ["inspect", "inspection", "inspected"],
        "resurface": ["resurface", "resurfaced", "resurfacing"],
        "adjust": ["adjust", "adjusted", "adjustment"],
        "tighten": ["tighten", "tightened"],
        "clean": ["clean", "cleaned"],
        "recharge": ["recharge", "recharged", "recharge system"],
    },
    "operating_condition": {
        "cold_start": ["cold start", "on cold start", "during cold start"],
        "acceleration": ["during acceleration", "under acceleration", "when accelerating"],
        "idle": ["at idle", "while idling", "idle"],
        "braking": ["when braking", "during braking", "under braking"],
        "highway": ["highway driving", "on the highway"],
    },
    "location": {
        "engine_bay": ["engine bay", "under hood", "front of the engine"],
        "front_left": ["front left", "left front"],
        "front_right": ["front right", "right front"],
        "rear_left": ["rear left"],
        "rear_right": ["rear right"],
        "exhaust_system": ["exhaust", "exhaust system", "muffler"],
    },
    "diagnostic_finding": {
        "abnormal_slack": ["abnormal timing chain slack", "chain slack"],
        "cavitation_damage": ["cavitation damage", "impeller damage"],
        "pad_thickness_low": ["pad thickness", "thickness measured"],
        "confirmed_failure": ["failure confirmed", "confirmed failure", "confirmed"],
    },
    "failure_mode": {
        "leakage": [
            "coolant leakage",
            "oil leakage",
            "fluid leakage",
            "leaking from",
            "leak from",
            "seal leak",
        ],
        "wear": ["excessive wear", "worn out", "worn component", "metal shavings"],
        "fracture": ["fractured", "cracked component", "broken component"],
        "contamination": ["contaminated", "contamination", "debris in"],
        "electrical_failure": ["electrical failure", "charging failure", "battery failure"],
        "seal_failure": ["seal failure", "failed seal", "gasket failure"],
        "timing_skip": ["timing skip", "skipped timing", "timing chain stretch"],
    },
}

# Phrases indicating heavy engine work vs lighter repairs
HEAVY_REPAIR_TERMS: Final[frozenset[str]] = frozenset(
    {
        "engine block",
        "complete engine",
        "engine replacement",
        "long block",
        "short block",
    }
)

LIGHT_REPAIR_TERMS: Final[frozenset[str]] = frozenset(
    {
        "tensioner",
        "timing chain",
        "brake pad",
        "water pump",
        "alternator",
        "actuator",
        "end link",
    }
)

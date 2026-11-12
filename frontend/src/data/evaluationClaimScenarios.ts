import type { NewClaimFormData } from "./sampleNewClaim";

export type EvaluationScenarioId =
  | "inspection_confirmed"
  | "supported_dealer"
  | "elevated_costs"
  | "thin_evidence";

export type EvaluationScenario = {
  id: EvaluationScenarioId;
  title: string;
  subtitle: string;
  /** What reviewers should expect after full assessment (TV + ML + rules). */
  expectedOutcome: string;
  form: NewClaimFormData;
  tips: string[];
};

const BASE_VEHICLE = {
  vin: "1FTFW1E87PKD41286",
  year: "2023",
  make: "Ford",
  model: "F-150",
  category: "BRAKING",
  mileage: "28500",
  engine_type: "3.5L EcoBoost",
} as const;

/** Demo-first: aligned squeal/brake narrative + pad mm — expect Technical SUPPORTED (not Questionable). */
export const SCENARIO_INSPECTION_CONFIRMED: EvaluationScenario = {
  id: "inspection_confirmed",
  title: "Inspection confirmed (green TV)",
  subtitle: "Aligned complaint/diagnosis · pad measurements",
  expectedOutcome:
    "Technical validation SUPPORTED via claim-attested measurements (rule R_CLAIM_ATTESTED_INSPECTION). Use for demos where Questionable is not desired.",
  tips: [
    "Re-run assessment after submit so stages refresh (re-run sends force_refresh).",
    "Best demo preset when financial ML and LLM options are on.",
  ],
  form: {
    repair_order: "RO-EVAL-GREEN",
    ...BASE_VEHICLE,
    parts_cost: "425.00",
    labour_hours: "3.25",
    complaint:
      "Front brake squeal when braking at low speed; mild vibration through the brake pedal. Noise began around 28,500 miles.",
    technician_diagnosis:
      "Road test confirmed front brake squeal. Measured front brake pad thickness: inner 1.2 mm (spec minimum 2.0 mm), outer 3.1 mm. Front rotors within resurface tolerance; caliper slides free; no brake fluid leak; no ABS DTCs.",
    repair:
      "Replace front brake pads (HL3Z-2001-D) and resurface front rotors. Inspect caliper slide pins and bleed brakes if fluid is contaminated.",
  },
};

/** Strong narrative + measurements; costs tuned for experimental ML “within range”. */
export const SCENARIO_SUPPORTED_DEALER: EvaluationScenario = {
  id: "supported_dealer",
  title: "Dealer-supported braking",
  subtitle: "Measurements on claim · costs near model band",
  expectedOutcome:
    "Technical validation usually favorable; RAG aligns with DOC-002-style evidence; financial ML often within expected range (enable experimental models + financial validation on run).",
  tips: [
    "Turn on Financial validation (ML) in assessment options.",
    "LLM may still fail validation with qwen-coder-2 — rules + TV remain authoritative.",
  ],
  form: {
    repair_order: "RO-EVAL-SUPPORTED",
    ...BASE_VEHICLE,
    parts_cost: "425.00",
    labour_hours: "3.25",
    complaint:
      "Squealing noise from the front wheels when braking at low speed. Customer reports the sound started near 28,000 miles.",
    technician_diagnosis:
      "Measured front brake pad thickness: inner 1.2 mm (minimum spec 2.0 mm), outer 3.1 mm. Rotors show minor scoring within resurfacing tolerance. Caliper slides move freely; no hydraulic fault on road test. No ABS fault codes.",
    repair:
      "Replace front brake pads (HL3Z-2001-D) and resurface rotors. Verify caliper slide pins and flush brake fluid if contaminated.",
  },
};

/** Same repair story; submitted costs above typical model prediction. */
export const SCENARIO_ELEVATED_COSTS: EvaluationScenario = {
  id: "elevated_costs",
  title: "Elevated parts & labour",
  subtitle: "Solid diagnosis · costs flagged by ML",
  expectedOutcome:
    "Technical path similar to supported case; financial ML should show material variance (outside expected range) with experimental models enabled.",
  tips: ["Compare parts/labour variance in the full assessment trace → Decision tab.", "Use for reviewer cost challenge workflows."],
  form: {
    repair_order: "RO-EVAL-ELEVATED",
    ...BASE_VEHICLE,
    parts_cost: "720.00",
    labour_hours: "7.0",
    complaint:
      "Squealing noise from the front wheels when braking at low speed. Customer reports the sound started near 28,000 miles.",
    technician_diagnosis:
      "Measured front brake pad thickness: inner 1.2 mm (minimum spec 2.0 mm), outer 3.1 mm. Rotors glazed with heat spots within resurfacing tolerance. Caliper slides move freely; no hydraulic fault on road test.",
    repair:
      "Replace front brake pads (HL3Z-2001-D) and resurface rotors. Replace caliper slide pin kit and flush brake fluid.",
  },
};

/** Matches CLM-0021-style submissions — vague measurements, gap for TV rules. */
export const SCENARIO_THIN_EVIDENCE: EvaluationScenario = {
  id: "thin_evidence",
  title: "Thin evidence (current flow)",
  subtitle: "No pad measurements · more review gaps",
  expectedOutcome:
    "Often INSUFFICIENT_EVIDENCE (e.g. R_PROCEDURE_THRESHOLD_UNKNOWN); human review required; financial may still run if enabled.",
  tips: [
    "Represents claims like CLM-0021 without uploaded measurements.",
    "Run assessment to compare with the supported dealer scenario.",
  ],
  form: {
    repair_order: "RO-2026-0412",
    ...BASE_VEHICLE,
    parts_cost: "320.00",
    labour_hours: "2.5",
    complaint:
      "Squealing noise from the front wheels when braking at low speed. Customer reports the sound started after 28,000 miles.",
    technician_diagnosis:
      "Front pads below minimum thickness; rotors glazed with heat spots. Caliper slides move freely; no hydraulic fault found on road test.",
    repair:
      "Replace front brake pads and resurface rotors. Verify caliper slide pins and flush brake fluid if contaminated.",
  },
};

export const EVALUATION_SCENARIOS: EvaluationScenario[] = [
  SCENARIO_INSPECTION_CONFIRMED,
  SCENARIO_SUPPORTED_DEALER,
  SCENARIO_ELEVATED_COSTS,
  SCENARIO_THIN_EVIDENCE,
];

export function getEvaluationScenario(id: string | null | undefined): EvaluationScenario | undefined {
  if (!id) return undefined;
  return EVALUATION_SCENARIOS.find((s) => s.id === id);
}

import { SCENARIO_THIN_EVIDENCE } from "./evaluationClaimScenarios";

/** Default demo payload — thin-evidence braking scenario (see evaluation scenarios). */

/** Internal repair order reference — generated when the form opens (real API will assign on submit). */
export function generateRepairOrder(): string {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  const d = String(now.getDate()).padStart(2, "0");
  const seq = String(now.getTime() % 10000).padStart(4, "0");
  return `RO-${y}${m}${d}-${seq}`;
}

export type NewClaimFormData = {
  repair_order: string;
  vin: string;
  year: string;
  make: string;
  model: string;
  category: string;
  mileage: string;
  engine_type: string;
  parts_cost: string;
  labour_hours: string;
  complaint: string;
  technician_diagnosis: string;
  repair: string;
};

export const SAMPLE_NEW_CLAIM: NewClaimFormData = { ...SCENARIO_THIN_EVIDENCE.form };

export const EMPTY_NEW_CLAIM: NewClaimFormData = {
  repair_order: "",
  vin: "",
  year: "",
  make: "",
  model: "",
  category: "ENGINE",
  mileage: "",
  engine_type: "",
  parts_cost: "",
  labour_hours: "",
  complaint: "",
  technician_diagnosis: "",
  repair: "",
};

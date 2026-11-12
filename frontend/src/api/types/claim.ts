export type ClaimStatus =
  | "SUBMITTED"
  | "UNDER_REVIEW"
  | "PENDING_INFORMATION"
  | "COMPLETED"
  | "CLOSED";

export interface Vehicle {
  vehicle_id: string;
  vin?: string | null;
  make: string;
  model: string;
  model_year: number;
  engine_type?: string | null;
  mileage?: number | null;
}

export interface Repair {
  repair_category: string;
  part_number?: string | null;
  part_description: string;
  recommended_action: string;
}

export interface ClaimInput {
  claim_id: string;
  submission_date: string;
  vehicle: Vehicle;
  customer_complaint: string;
  technician_diagnosis: string;
  recommended_repair: Repair;
  submitted_parts_cost: string;
  submitted_labour_hours: string;
  currency: string;
  supporting_document_ids: string[];
  claim_status: ClaimStatus;
}

# CLAIMWISE Data Dictionary

## Vehicle

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| vehicle_id | string | yes | Non-blank, trimmed | Unique vehicle identifier |
| vin | string | no | Blank becomes None | Vehicle Identification Number (optional for synthetic data) |
| make | string | yes | Non-blank, trimmed | Manufacturer (e.g. Ford) |
| model | string | yes | Non-blank, trimmed | Vehicle model (e.g. Mustang) |
| model_year | integer | yes | 1980 to current year + 1 | Manufacturing year |
| engine_type | string | no | Blank becomes None | Engine description (e.g. 2.3L EcoBoost I4) |
| mileage | integer | no | >= 0 | Odometer reading at time of claim |

## Repair

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| repair_category | string | yes | Stripped, uppercased, non-blank | Category such as ENGINE, BRAKING, TRANSMISSION (open, not a closed enum) |
| part_number | string | no | Blank becomes None | Manufacturer part number |
| part_description | string | yes | Non-blank, trimmed | Human-readable part name |
| recommended_action | string | yes | Non-blank, trimmed | Technician's recommended repair action |

## ClaimInput

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| claim_id | string | yes | Non-blank, trimmed | Unique claim identifier |
| submission_date | datetime | yes | Must be timezone-aware (UTC offset required) | When the claim was submitted |
| vehicle | Vehicle | yes | Nested validation | Vehicle details |
| customer_complaint | string | yes | Non-blank | Original customer complaint text (preserved as written) |
| technician_diagnosis | string | yes | Non-blank | Technician's diagnosis text (preserved as written) |
| recommended_repair | Repair | yes | Nested validation | Technician's recommended repair |
| submitted_parts_cost | Decimal | yes | >= 0 | Parts cost submitted by the dealer |
| submitted_labour_hours | Decimal | yes | >= 0 | Labour hours submitted by the dealer |
| currency | string | yes | 3-letter uppercase (e.g. USD, CAD) | Currency code for costs |
| supporting_document_ids | list[string] | no | Defaults to empty list | IDs of attached evidence documents |
| claim_status | ClaimStatus | no | SUBMITTED, UNDER_REVIEW, PENDING_INFORMATION, COMPLETED, CLOSED | Current processing status |

## RepairDocument

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| document_id | string | yes | Non-blank, trimmed | Unique document identifier |
| claim_id | string | no | | Associated claim (null for reference documents) |
| document_type | DocumentType | yes | TECHNICIAN_REPORT, REPAIR_HISTORY, DIAGNOSTIC_REPORT, PART_REFERENCE, LABOUR_REFERENCE | Type of document |
| title | string | yes | Non-blank, trimmed | Document title |
| content | string | yes | Non-blank | Full document text |
| vehicle_make | string | no | | Manufacturer filter for retrieval |
| vehicle_model | string | no | | Model filter for retrieval |
| model_year | integer | no | | Year filter for retrieval |
| repair_category | string | no | | Category filter for retrieval |
| part_number | string | no | | Part number filter for retrieval |
| repair_outcome | string | no | | What actually happened (for historical records) |
| verification_status | VerificationStatus | no | VERIFIED, UNVERIFIED, PENDING | Whether the document has been verified |
| created_at | datetime | yes | Must be timezone-aware | Document creation timestamp |

## TechnicalValidationResult

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| claim_id | string | yes | Claim being validated |
| technical_status | TechnicalStatus | yes | SUPPORTED, QUESTIONABLE, INSUFFICIENT_EVIDENCE, NEEDS_REVIEW |
| diagnosis_summary | string | yes | Summary of the extracted diagnosis |
| repair_assessment | string | yes | Assessment of the recommended repair against evidence |
| supporting_evidence | list[EvidenceItem] | no | Evidence that supports the repair |
| contradictory_evidence | list[EvidenceItem] | no | Evidence that contradicts the repair |
| missing_evidence | list[string] | no | Evidence that should exist but was not found |
| confidence | float | no | 0.0–1.0; optional until calibrated |
| explanation | string | no | Human-readable explanation |

## EvidenceItem

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| document_id | string | yes | Source document |
| relevant_excerpt | string | yes | Relevant text from the document |
| relevance_score | float | no | 0.0–1.0 |
| evidence_type | string | yes | supporting, contradictory, or neutral |

## FinancialValidationResult

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| claim_id | string | yes | Claim being validated |
| submitted_parts_cost | Decimal | yes | Dealer's submitted parts cost |
| predicted_parts_cost | Decimal | no | ML-predicted parts cost (Phase 5+) |
| submitted_labour_hours | Decimal | yes | Dealer's submitted labour hours |
| predicted_labour_hours | Decimal | no | ML-predicted labour hours (Phase 5+) |
| parts_discrepancy_pct | Decimal | no | Percentage difference for parts |
| labour_discrepancy_pct | Decimal | no | Percentage difference for labour |
| parts_prediction_interval | PredictionInterval | no | Low/typical/high range for parts |
| labour_prediction_interval | PredictionInterval | no | Low/typical/high range for labour |
| financial_status | FinancialStatus | yes | WITHIN_EXPECTED_RANGE, OUTSIDE_EXPECTED_RANGE, INSUFFICIENT_DATA, NEEDS_REVIEW |
| explanation | string | no | Human-readable explanation |

## ClaimRecommendation

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| claim_id | string | yes | Claim being assessed |
| technical_validation | TechnicalValidationResult | no | Technical verdict (Phase 4+) |
| financial_validation | FinancialValidationResult | no | Financial verdict (Phase 5+) |
| overall_recommendation | OverallRecommendation | yes | PROCEED_TO_REVIEW, REQUEST_MORE_EVIDENCE, FLAG_FOR_REVIEW, INSUFFICIENT_INFORMATION |
| recommendation_reasons | list[string] | no | Reasons behind the recommendation |
| evidence_document_ids | list[string] | no | Documents cited as evidence |
| missing_information | list[string] | no | Information that should be provided |
| human_review_required | bool | no | Always True; system never auto-decides |
| generated_at | datetime | yes | When the recommendation was generated |

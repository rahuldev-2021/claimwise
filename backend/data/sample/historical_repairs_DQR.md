# Historical repairs — data quality report

Source: `repair_documents.json` (12 documents, synthetic sample).  
Records created: **4**. Excluded: **8**.

## Claim ID inconsistency

- **DOC-008** and **DOC-010** both list `claim_id` CLM-008 but describe different model years (2021 vs 2019).
- **HR-010** uses `source_claim_id: null` until manually reconciled.

## Classifications

| Document | Classification |
|----------|----------------|
| DOC-001–008 (except completed) | DIAGNOSTIC_OR_TECHNICIAN_REPORT — no historical row |
| DOC-002, 003, 009, 010 | COMPLETED_REPAIR_WITH_OUTCOME → HR row |
| DOC-011 | PARTS_REFERENCE — excluded |
| DOC-012 | LABOUR_REFERENCE — excluded |

All rows: `synthetic: true`.

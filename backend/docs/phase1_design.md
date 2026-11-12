# CLAIMWISE Phase 1 Design Decisions

## Why Pydantic v2

Pydantic v2 provides runtime validation, clear error messages, and JSON serialization in one package. Using `ConfigDict(extra="forbid")` on inbound schemas catches unexpected fields early. Field validators normalize text (strip, uppercase) at the boundary so downstream code never handles raw whitespace.

## Why Decimal for monetary values

Floating-point arithmetic introduces rounding errors that are unacceptable in financial comparisons. A submitted cost of $4,600.00 must compare exactly with a predicted cost, not differ by a fraction of a cent. All costs and labour hours use `Decimal`. Sample JSON stores these as strings to avoid float parsing.

## Why timezone-aware datetimes

Claims arrive from multiple time zones. Storing naive datetimes would make submission ordering ambiguous. All datetime fields require a UTC offset. Sample data uses ISO-8601 with `Z` (UTC).

## Why separate technical and financial validation schemas

The system asks two independent questions:

1. Does the complaint and diagnosis support the recommended repair? (Technical validation)
2. Is the submitted cost and labour reasonable for that repair? (Financial validation)

A repair can be technically supported but financially overpriced (timing chain replacement at triple the usual cost), or financially reasonable but technically unjustified (an engine block replacement priced correctly but not warranted by a rattling noise).

Keeping these as separate schemas and separate modules prevents one check from silently influencing the other. The recommendation module is the only place they are combined.

## Why Protocols instead of abstract base classes

Python `Protocol` supports structural subtyping: a class satisfies the interface if it has the right methods, without inheriting from a base. This means module implementations can live in separate packages and do not need to import the interface definition at runtime, reducing coupling.

## Why repair_category is not a closed enum

New repair categories (EXHAUST, STEERING, FUEL_SYSTEM) will appear as the dataset grows. A closed enum would require a code change and redeployment for each new category. Instead, the field is validated as a non-blank uppercased string. Known categories are documented but not enforced as the only allowed values.

## Why the recommendation never approves or rejects

CLAIMWISE is a decision-support system. The `OverallRecommendation` enum contains PROCEED_TO_REVIEW, REQUEST_MORE_EVIDENCE, FLAG_FOR_REVIEW, and INSUFFICIENT_INFORMATION. None of these is APPROVE or REJECT. The human claims agent retains final authority.

## Status label mapping

Phase 1 uses `QUESTIONABLE` for the technical status where earlier architecture discussions used `POTENTIALLY_UNSUPPORTED`. The meaning is the same: the notes or similar cases point to a smaller or different repair, and the claim needs a closer look. The mapping:

| Phase 1 schema | Architecture diagram |
|----------------|---------------------|
| SUPPORTED | Supported |
| QUESTIONABLE | Potentially excessive / Potentially unsupported |
| INSUFFICIENT_EVIDENCE | Insufficient evidence |
| NEEDS_REVIEW | Needs more evidence |

## Why sample data includes incomplete claims

Claims CLM-009, CLM-010, and CLM-011 have empty `supporting_document_ids` or sparse diagnostic notes. These exist so that later phases can test the system's ability to return INSUFFICIENT_EVIDENCE or REQUEST_MORE_EVIDENCE instead of forcing a verdict from thin data.

## Repository pattern

The `SampleClaimRepository` reads JSON files on disk. The `ClaimService` wraps it. In later phases the repository will be replaced by a BigQuery or PostgreSQL implementation without changing the service or the API routes.

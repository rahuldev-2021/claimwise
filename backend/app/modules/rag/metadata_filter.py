"""Metadata filtering for retrieval.

Builds ChromaDB ``where`` clauses from a set of requested filter values.
Behaviour is explicit and conservative:

* Only fields that are actually present in the request are filtered on — we
  never fabricate a filter for a missing value.
* Matching is **exact** against the stored metadata value (strings are
  whitespace-stripped).  ChromaDB performs exact equality, so we do not
  case-fold: a filter on ``vehicle_make="Ford"`` matches documents stored with
  ``vehicle_make="Ford"`` and not ``"ford"``.  This keeps behaviour
  predictable and testable.
* A document that *lacks* an optional metadata field will not match a filter
  on that field.  This is intentional: filtering on ``vehicle_make=Ford``
  should not return documents whose make is unknown.  Callers that want to
  keep unfiltered evidence simply omit that field from the request.
"""

from typing import Optional


def _normalize(field: str, value: object) -> object:
    """Strip surrounding whitespace from string values; pass others through."""
    if isinstance(value, str):
        return value.strip()
    return value


def build_where(
    filters: dict[str, object] | None,
) -> Optional[dict[str, object]]:
    """Build a ChromaDB ``where`` clause from a flat filter dict.

    Returns ``None`` when there is nothing to filter on.  Supports:

    * ``{"field": value}`` — equality.
    * ``{"field": [v1, v2]}`` — ``$in`` (any of).
    """
    if not filters:
        return None

    where: dict[str, object] = {}
    for field, value in filters.items():
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            values = list(value)
            if not values:
                continue
            normalized = [_normalize(field, v) for v in values]
            where[field] = {"$in": normalized}
        else:
            where[field] = _normalize(field, value)

    if not where:
        return None
    if len(where) == 1:
        return where
    return {"$and": [{key: val} for key, val in where.items()]}


def build_from_claim(
    claim: object,
    *,
    fields: tuple[str, ...] = ("repair_category",),
) -> Optional[dict[str, object]]:
    """Build a filter from a claim's structured fields.

    By default only ``repair_category`` is used — a light filter that keeps
    the small sample corpus useful while still scoping results to the relevant
    repair domain.  Additional fields (``vehicle_make``, ``vehicle_model``,
    ``model_year``) can be requested, but each one narrows results and may
    exclude useful evidence when a document lacks that metadata.
    """
    filters: dict[str, object] = {}

    repair = getattr(claim, "recommended_repair", None)
    if "repair_category" in fields and repair is not None:
        category = getattr(repair, "repair_category", None)
        if category:
            filters["repair_category"] = category

    vehicle = getattr(claim, "vehicle", None)
    if vehicle is not None:
        if "vehicle_make" in fields and getattr(vehicle, "make", None):
            filters["vehicle_make"] = vehicle.make
        if "vehicle_model" in fields and getattr(vehicle, "model", None):
            filters["vehicle_model"] = vehicle.model
        if "model_year" in fields and getattr(vehicle, "model_year", None):
            filters["model_year"] = vehicle.model_year

    return build_where(filters)

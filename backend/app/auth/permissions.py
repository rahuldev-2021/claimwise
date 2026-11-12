"""RBAC: roles to permission strings."""

from typing import Iterable

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "customer": frozenset({"claims:read"}),
    "dealer_technician": frozenset(
        {
            "claims:read",
            "claims:submit",
            "claims:update_own",
            "documents:upload",
        }
    ),
    "warranty_agent": frozenset(
        {
            "claims:read",
            "claims:submit",
            "claims:assess",
            "claims:review",
            "feedback:write",
            "documents:upload",
            "api:read",
        }
    ),
    "developer": frozenset({"claims:read", "claims:assess", "api:read"}),
    "admin": frozenset(
        {
            "claims:read",
            "claims:submit",
            "claims:assess",
            "claims:review",
            "feedback:write",
            "documents:upload",
            "api:read",
            "admin:org",
        }
    ),
    "super_admin": frozenset(
        {
            "claims:read",
            "claims:submit",
            "claims:assess",
            "claims:review",
            "feedback:write",
            "documents:upload",
            "api:read",
            "admin:org",
            "admin:users",
            "admin:system",
        }
    ),
}


def permissions_for_roles(roles: Iterable[str]) -> list[str]:
    perms: set[str] = set()
    for role in roles:
        perms.update(ROLE_PERMISSIONS.get(role, frozenset()))
    return sorted(perms)


def is_admin_role(roles: Iterable[str]) -> bool:
    r = set(roles)
    return bool(r.intersection({"admin", "super_admin"}))

"""Organization-scoped access helpers."""

from app.auth.dependencies import CurrentUser


def is_super_admin(user: CurrentUser) -> bool:
    return "super_admin" in user.roles


def can_access_org(user: CurrentUser, org_id: str) -> bool:
    if is_super_admin(user):
        return True
    if not org_id:
        return False
    return user.org_id == org_id

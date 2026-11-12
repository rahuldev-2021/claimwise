"""JWT auth dependencies and RBAC."""

from typing import Annotated, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import decode_access_token
from app.auth.mongodb import get_auth_db
from app.auth.permissions import permissions_for_roles
from app.core.config import Settings, get_settings

_bearer = HTTPBearer(auto_error=False)


class CurrentUser:
    def __init__(
        self,
        user_id: str,
        email: str,
        org_id: str,
        roles: list[str],
        permissions: list[str],
        session_id: str,
    ) -> None:
        self.user_id = user_id
        self.email = email
        self.org_id = org_id
        self.roles = roles
        self.permissions = permissions
        self.session_id = session_id


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_access_token(settings, credentials.credentials)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    db = get_auth_db(settings)
    user = db["users"].find_one({"_id": payload["sub"]})
    if not user or user.get("status") != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")

    return CurrentUser(
        user_id=payload["sub"],
        email=user.get("email", ""),
        org_id=payload.get("org_id", ""),
        roles=list(payload.get("roles") or []),
        permissions=list(payload.get("permissions") or permissions_for_roles(payload.get("roles") or [])),
        session_id=payload.get("session_id", ""),
    )


def require_permissions(*required: str) -> Callable[..., CurrentUser]:
    def _dep(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        missing = [p for p in required if p not in user.permissions]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing)}",
            )
        return user

    return _dep

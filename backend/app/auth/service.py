"""Login authentication and session token issuance."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pymongo.database import Database

from app.auth.jwt import create_access_token
from app.auth.password import verify_password
from app.auth.permissions import permissions_for_roles
from app.auth.refresh_tokens import RefreshTokenService
from app.core.config import Settings


class AuthenticationError(Exception):
    pass


class OrgAccessError(Exception):
    pass


def normalize_email(email: str) -> str:
    return email.strip().lower()


def authenticate_user(db: Database, email: str, password: str) -> dict[str, Any]:
    normalized = normalize_email(email)
    user = db["users"].find_one({"email": normalized})
    if not user or user.get("status") != "active":
        raise AuthenticationError("Invalid email or password")
    if not verify_password(user["password_hash"], password):
        raise AuthenticationError("Invalid email or password")
    membership = db["org_memberships"].find_one(
        {"user_id": user["_id"], "status": "active"},
    )
    if not membership:
        raise OrgAccessError("No active organization membership")
    org = db["organizations"].find_one({"_id": membership["org_id"]})
    if not org or org.get("status") != "active":
        raise OrgAccessError("Organization is not active")
    return {
        "user": user,
        "membership": membership,
        "org": org,
    }


def create_session_tokens(
    db: Database,
    settings: Settings,
    *,
    user: dict[str, Any],
    membership: dict[str, Any],
    org: dict[str, Any],
    device_id: str | None = None,
) -> tuple[str, int, str]:
    """Return access_token, expires_in, refresh_token_raw."""
    roles = list(membership.get("roles") or [])
    permissions = permissions_for_roles(roles)
    refresh_svc = RefreshTokenService(db, settings)
    refresh_raw, session_id, _family = refresh_svc.create_session(
        user_id=user["_id"],
        org_id=org["_id"],
        device_id=device_id or str(uuid4()),
    )
    access, expires_in = create_access_token(
        settings,
        user_id=user["_id"],
        org_id=org["_id"],
        roles=roles,
        permissions=permissions,
        session_id=session_id,
    )
    db["users"].update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login_at": datetime.now(timezone.utc)}},
    )
    return access, expires_in, refresh_raw

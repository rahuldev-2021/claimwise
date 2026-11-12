"""HS256 access JWT creation and validation."""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import jwt

from app.core.config import Settings


class JwtConfigurationError(RuntimeError):
    pass


def _require_secret(settings: Settings) -> str:
    secret = settings.JWT_SECRET.strip()
    if not secret:
        raise JwtConfigurationError("JWT_SECRET is required for authentication")
    return secret


def create_access_token(
    settings: Settings,
    *,
    user_id: str,
    org_id: str,
    roles: list[str],
    permissions: list[str],
    session_id: str,
) -> tuple[str, int]:
    now = datetime.now(timezone.utc)
    expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    exp = now + timedelta(minutes=expire_minutes)
    payload: dict[str, Any] = {
        "sub": user_id,
        "org_id": org_id,
        "roles": roles,
        "permissions": permissions,
        "session_id": session_id,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": str(uuid4()),
    }
    token = jwt.encode(payload, _require_secret(settings), algorithm="HS256")
    return token, expire_minutes * 60


def decode_access_token(settings: Settings, token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        _require_secret(settings),
        algorithms=["HS256"],
        audience=settings.JWT_AUDIENCE,
        issuer=settings.JWT_ISSUER,
    )

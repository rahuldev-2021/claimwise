"""Refresh token rotation, family revocation, and theft detection."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from pymongo.database import Database

from app.core.config import Settings


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def mint_refresh_token() -> str:
    return secrets.token_urlsafe(32)


class RefreshTokenService:
    def __init__(self, db: Database, settings: Settings) -> None:
        self._col = db["refresh_sessions"]
        self._settings = settings

    def create_session(
        self,
        *,
        user_id: str,
        org_id: str,
        device_id: str,
        family_id: str | None = None,
    ) -> tuple[str, str, str]:
        raw = mint_refresh_token()
        session_id = str(uuid4())
        family = family_id or str(uuid4())
        expires = datetime.now(timezone.utc) + timedelta(days=self._settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        doc = {
            "_id": session_id,
            "token_hash": _hash_token(raw),
            "user_id": user_id,
            "org_id": org_id,
            "session_id": session_id,
            "device_id": device_id,
            "family_id": family,
            "expires_at": expires,
            "revoked": False,
            "rotated": False,
            "replaced_by": None,
            "created_at": datetime.now(timezone.utc),
        }
        self._col.insert_one(doc)
        return raw, session_id, family

    def _get_by_hash(self, token_hash: str) -> Optional[dict[str, Any]]:
        return self._col.find_one({"token_hash": token_hash})

    def rotate(self, raw_refresh: str, *, device_id: str) -> tuple[str, str, str, str]:
        """Returns new_raw, session_id, family_id, user_id; revokes old token."""
        token_hash = _hash_token(raw_refresh)
        doc = self._get_by_hash(token_hash)
        if not doc:
            raise ValueError("Invalid refresh token")

        if doc.get("revoked"):
            self._revoke_family(doc["family_id"])
            raise ValueError("Session invalidated. Please sign in again.")

        expires: datetime = doc["expires_at"]
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < datetime.now(timezone.utc):
            raise ValueError("Refresh token expired")

        self._col.update_one({"_id": doc["_id"]}, {"$set": {"rotated": True, "revoked": True}})

        new_raw, session_id, family = self.create_session(
            user_id=doc["user_id"],
            org_id=doc["org_id"],
            device_id=device_id,
            family_id=doc["family_id"],
        )
        self._col.update_one(
            {"_id": doc["_id"]},
            {"$set": {"replaced_by": session_id}},
        )
        return new_raw, session_id, family, doc["user_id"]

    def _revoke_family(self, family_id: str) -> None:
        self._col.update_many(
            {"family_id": family_id},
            {"$set": {"revoked": True}},
        )

    def revoke_token(self, raw_refresh: str) -> None:
        token_hash = _hash_token(raw_refresh)
        self._col.update_one({"token_hash": token_hash}, {"$set": {"revoked": True}})

    def revoke_all_for_user(self, user_id: str) -> int:
        result = self._col.update_many({"user_id": user_id}, {"$set": {"revoked": True}})
        return int(result.modified_count)

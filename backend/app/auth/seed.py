"""Bootstrap organization, roles, and admin user on startup."""

import logging
from uuid import uuid4

from pymongo.database import Database

from app.auth.password import hash_password
from app.auth.service import normalize_email
from app.core.config import Settings

logger = logging.getLogger(__name__)


def ensure_indexes(db: Database) -> None:
    db["users"].create_index("email", unique=True)
    db["org_memberships"].create_index([("user_id", 1), ("org_id", 1)], unique=True)
    db["refresh_sessions"].create_index("token_hash", unique=True)
    db["refresh_sessions"].create_index("user_id")


def seed_auth_data(db: Database, settings: Settings) -> None:
    ensure_indexes(db)

    org_id = "org_default"
    org = db["organizations"].find_one({"_id": org_id})
    if not org:
        db["organizations"].insert_one(
            {
                "_id": org_id,
                "name": settings.AUTH_BOOTSTRAP_ORG_NAME,
                "status": "active",
            }
        )
        logger.info("Created bootstrap organization %s", org_id)

    email = normalize_email(settings.AUTH_BOOTSTRAP_ADMIN_EMAIL)
    user = db["users"].find_one({"email": email})
    if not user:
        user_id = f"user_{uuid4().hex[:12]}"
        db["users"].insert_one(
            {
                "_id": user_id,
                "email": email,
                "password_hash": hash_password(settings.AUTH_BOOTSTRAP_ADMIN_PASSWORD),
                "status": "active",
                "display_name": "Bootstrap Admin",
            }
        )
        db["org_memberships"].insert_one(
            {
                "user_id": user_id,
                "org_id": org_id,
                "roles": ["super_admin"],
                "status": "active",
            }
        )
        logger.info("Seeded bootstrap admin user %s (change password in production)", email)

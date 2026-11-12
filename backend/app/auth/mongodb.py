"""MongoDB client for auth data."""

from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import Settings, get_settings


@lru_cache
def get_mongo_client() -> MongoClient:
    settings = get_settings()
    return MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=3000)


def get_auth_db(settings: Settings | None = None) -> Database:
    settings = settings or get_settings()
    return get_mongo_client()[settings.MONGODB_DB_NAME]

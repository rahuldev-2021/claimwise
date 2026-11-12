"""In-memory login rate limiter per client IP."""

import time
from collections import defaultdict
from threading import Lock

_WINDOW_SECONDS = 300
_MAX_ATTEMPTS = 10

_attempts: dict[str, list[float]] = defaultdict(list)
_lock = Lock()


def client_ip_from_request(headers: dict[str, str], client_host: str | None) -> str:
    forwarded = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return client_host or "unknown"


def check_login_rate_limit(ip: str) -> None:
    now = time.time()
    with _lock:
        bucket = _attempts[ip]
        bucket[:] = [t for t in bucket if now - t < _WINDOW_SECONDS]
        if len(bucket) >= _MAX_ATTEMPTS:
            from fastapi import HTTPException

            raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")
        bucket.append(now)

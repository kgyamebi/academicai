from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.config import get_settings
from app.core.logging import get_logger
from app.models.user import User

log = get_logger("rate_limit")

_WINDOW = 60
_hits: dict[str, deque[float]] = defaultdict(deque)

LIMITS = {
    "guest": {"login": 10, "signup": 8, "upload": 8, "analysis": 4, "coach": 4, "default": 60},
    "free": {"login": 20, "signup": 10, "upload": 20, "analysis": 8, "coach": 8, "default": 120},
    "student": {"login": 30, "upload": 40, "analysis": 20, "coach": 20, "default": 240},
    "pro": {"login": 40, "upload": 80, "analysis": 40, "coach": 40, "default": 400},
    "power": {"login": 60, "upload": 120, "analysis": 80, "coach": 80, "default": 800},
    "institution": {"login": 80, "upload": 200, "analysis": 120, "coach": 120, "default": 1200},
    "admin": {"login": 80, "upload": 200, "analysis": 200, "coach": 200, "default": 2000},
}


def check_rate_limit(request: Request, bucket: str, user: User | None = None) -> None:
    role = "guest"
    if user and user.role:
        role = user.role.name
    elif user and not user.is_guest:
        role = "free"
    limits = LIMITS.get(role, LIMITS["guest"])
    max_hits = limits.get(bucket, limits["default"])
    ident = f"{role}:{bucket}:{user.id if user else request.client.host if request.client else 'anon'}"
    settings = get_settings()
    if settings.app_env == "test":
        return
    try:
        if _redis_hit(ident, max_hits):
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Please wait a moment and try again.")
        return
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        if settings.is_production:
            log.error("rate_limit_redis_unavailable", error=str(exc))
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Rate limiting is unavailable.") from exc
        log.warning("rate_limit_memory_fallback", error=str(exc))
    _memory_hit(ident, max_hits)


def _redis_hit(ident: str, max_hits: int) -> bool:
    from redis import Redis

    redis = Redis.from_url(get_settings().redis_url, socket_timeout=1)
    key = f"rl:{ident}"
    current = redis.incr(key)
    if current == 1:
        redis.expire(key, _WINDOW)
    return int(current) > max_hits


def _memory_hit(ident: str, max_hits: int) -> None:
    now = time.time()
    q = _hits[ident]
    while q and now - q[0] > _WINDOW:
        q.popleft()
    if len(q) >= max_hits:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Please wait a moment and try again.")
    q.append(now)

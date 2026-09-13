"""Process-local TTL cache for public metadata and other read-mostly data.

Not a cluster cache. Redis-backed AI responses live in ``app.services.ai.cache``.
"""

from __future__ import annotations

import time
from threading import Lock

from app.core.metrics import cache_hit, cache_miss

_lock = Lock()
_store: dict[str, tuple[float, object]] = {}
_MAX_KEYS = 256


def cache_get(key: str, *, bucket: str = "meta"):
    now = time.monotonic()
    with _lock:
        item = _store.get(key)
        if not item:
            cache_miss(bucket)
            return None
        expires, value = item
        if expires < now:
            _store.pop(key, None)
            cache_miss(bucket)
            return None
        cache_hit(bucket)
        return value


def cache_set(key: str, value: object, ttl_seconds: int, *, bucket: str = "meta") -> None:
    if ttl_seconds <= 0:
        return
    with _lock:
        _store[key] = (time.monotonic() + ttl_seconds, value)
        if len(_store) > _MAX_KEYS:
            oldest = sorted(_store.items(), key=lambda item: item[1][0])[:64]
            for stale, _ in oldest:
                _store.pop(stale, None)


def cache_clear() -> None:
    with _lock:
        _store.clear()

"""Shared AI prompt cache: Redis when available, in-process fallback, request collapsing."""

from __future__ import annotations

import json
import time
from concurrent.futures import Future
from threading import Lock

from app.config import get_settings
from app.core.metrics import cache_hit, cache_miss

_lock = Lock()
_store: dict[str, tuple[float, object]] = {}
_inflight: dict[str, list[Future]] = {}
_REDIS_PREFIX = "ai:cache:"


def cache_key(prompt: str, *, strong: bool) -> str:
    import hashlib

    raw = f"{int(strong)}:{prompt}".encode()
    return hashlib.sha256(raw).hexdigest()


def _to_ai_response(value: object):
    from app.services.ai.provider import AIResponse

    if isinstance(value, AIResponse):
        return value
    if isinstance(value, dict) and value.get("_t") == "AIResponse":
        return AIResponse(
            content=str(value.get("content") or ""),
            model=str(value.get("model") or ""),
            provider=str(value.get("provider") or ""),
            tokens=int(value.get("tokens") or 0),
            prompt_version=str(value.get("prompt_version") or ""),
        )
    return value


def _dump(value: object) -> str | None:
    from app.services.ai.provider import AIResponse

    if isinstance(value, AIResponse):
        return json.dumps(
            {
                "_t": "AIResponse",
                "content": value.content,
                "model": value.model,
                "provider": value.provider,
                "tokens": value.tokens,
                "prompt_version": value.prompt_version,
            }
        )
    return None


def _redis_get(key: str):
    try:
        from app.workers.queue import redis_client

        raw = redis_client().get(_REDIS_PREFIX + key)
        if not raw:
            return None
        return json.loads(raw)
    except Exception:  # noqa: BLE001
        return None


def _redis_set(key: str, value: object, ttl: int) -> None:
    payload = _dump(value)
    if not payload or ttl <= 0:
        return
    try:
        from app.workers.queue import redis_client

        redis_client().setex(_REDIS_PREFIX + key, ttl, payload)
    except Exception:  # noqa: BLE001
        return


def get_cached(key: str):
    settings = get_settings()
    ttl = settings.ai_cache_ttl_seconds
    if ttl <= 0:
        cache_miss("ai")
        return None
    remote = _redis_get(key)
    if remote is not None:
        cache_hit("ai")
        return _to_ai_response(remote)
    now = time.monotonic()
    with _lock:
        item = _store.get(key)
        if not item:
            cache_miss("ai")
            return None
        expires, value = item
        if expires < now:
            _store.pop(key, None)
            cache_miss("ai")
            return None
        cache_hit("ai")
        return value


def set_cached(key: str, value: object) -> None:
    settings = get_settings()
    ttl = settings.ai_cache_ttl_seconds
    if ttl <= 0:
        return
    _redis_set(key, value, ttl)
    with _lock:
        _store[key] = (time.monotonic() + ttl, value)
        if len(_store) > 512:
            oldest = sorted(_store.items(), key=lambda item: item[1][0])[:64]
            for stale, _ in oldest:
                _store.pop(stale, None)


def take_leadership(key: str) -> Future | None:
    """If another caller is filling this key, return a Future to wait on."""
    with _lock:
        waiters = _inflight.get(key)
        if waiters is not None:
            fut: Future = Future()
            waiters.append(fut)
            return fut
        _inflight[key] = []
        return None


def publish_result(key: str, value: object | None) -> None:
    with _lock:
        waiters = _inflight.pop(key, [])
    for fut in waiters:
        if not fut.done():
            fut.set_result(value)


def reset_cache() -> None:
    with _lock:
        _store.clear()
        waiters = list(_inflight.items())
        _inflight.clear()
    for _, pending in waiters:
        for fut in pending:
            if not fut.done():
                fut.set_result(None)
    try:
        from app.workers.queue import redis_client

        client = redis_client()
        for redis_key in client.scan_iter(match=_REDIS_PREFIX + "*", count=100):
            client.delete(redis_key)
    except Exception:  # noqa: BLE001
        return

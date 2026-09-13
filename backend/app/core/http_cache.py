"""CDN-compatible cache headers for public, cache-busting for tenant APIs.

A real CDN (Cloudflare/Fastly) is not required to prove header correctness.
Local nginx/Varnish should honor the same Cache-Control / Surrogate-Key values.
"""

from __future__ import annotations

from fastapi import Request, Response

from app.core.app_cache import cache_clear
from app.core.metrics import incr

PUBLIC_CACHE_TTL_SECONDS = 60
SURROGATE_KEY_PUBLIC = "public-meta"

_PUBLIC_PREFIX = "/api/public/"
_UNCACHED_PUBLIC = {"/api/public/analytics"}


def is_cdn_cacheable(request: Request) -> bool:
    if request.method != "GET":
        return False
    path = request.url.path
    if path in _UNCACHED_PUBLIC:
        return False
    return path.startswith(_PUBLIC_PREFIX)


def apply_cache_headers(request: Request, response: Response) -> None:
    if is_cdn_cacheable(request) and response.status_code == 200:
        ttl = PUBLIC_CACHE_TTL_SECONDS
        response.headers["Cache-Control"] = f"public, max-age={ttl}, stale-while-revalidate={ttl}"
        response.headers["CDN-Cache-Control"] = f"public, max-age={ttl}"
        response.headers["Surrogate-Control"] = f"max-age={ttl}"
        response.headers["Surrogate-Key"] = SURROGATE_KEY_PUBLIC
        response.headers["Vary"] = "Accept-Encoding"
        return
    response.headers["Cache-Control"] = "no-store"
    response.headers["CDN-Cache-Control"] = "no-store"


def invalidate_public_cache() -> None:
    """Drop in-process public metadata. Edge purge is a CDN API (live account)."""
    cache_clear()
    incr("cache.public.invalidate")


def cdn_asset_url(path: str) -> str:
    """Stable public URL prefix a CDN origin can map. Not a live CDN hostname."""
    cleaned = "/" + path.lstrip("/")
    return f"/cdn/public{cleaned}"

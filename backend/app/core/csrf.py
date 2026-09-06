from fastapi import HTTPException, Request, status

from app.core.cookies import CSRF_COOKIE
from app.core.security import constant_time_equals

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
EXEMPT_PREFIXES = (
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/guest",
    "/api/auth/refresh",
    "/api/auth/csrf",
    "/api/auth/password/forgot",
    "/api/auth/password/reset",
    "/api/auth/verify",
    "/api/billing/payments/webhook",
    "/api/billing/webhooks/",
    "/api/public/",
    "/api/health",
    "/api/reports/shared/",
)


def enforce_csrf(request: Request) -> None:
    if request.method in SAFE_METHODS:
        return
    path = request.url.path
    if any(path == prefix or path.startswith(prefix) for prefix in EXEMPT_PREFIXES):
        return
    if request.headers.get("authorization", "").lower().startswith("bearer "):
        return
    if not request.cookies.get("ac_access"):
        return
    cookie = request.cookies.get(CSRF_COOKIE, "")
    header = request.headers.get("x-csrf-token", "")
    if not cookie or not header or not constant_time_equals(cookie, header):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "CSRF validation failed.")

from fastapi import Response

from app.config import get_settings

ACCESS_COOKIE = "ac_access"
REFRESH_COOKIE = "ac_refresh"
CSRF_COOKIE = "ac_csrf"


def cookie_secure() -> bool:
    settings = get_settings()
    return settings.is_production or settings.cookie_secure


def set_auth_cookies(response: Response, access: str, refresh: str, csrf: str) -> None:
    settings = get_settings()
    secure = cookie_secure()
    response.set_cookie(
        ACCESS_COOKIE,
        access,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=settings.access_token_minutes * 60,
        path="/",
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=settings.refresh_token_days * 86400,
        path="/api/auth",
    )
    response.set_cookie(
        CSRF_COOKIE,
        csrf,
        httponly=False,
        secure=secure,
        samesite="lax",
        max_age=settings.refresh_token_days * 86400,
        path="/",
    )


def set_csrf_cookie(response: Response, csrf: str) -> None:
    settings = get_settings()
    response.set_cookie(
        CSRF_COOKIE,
        csrf,
        httponly=False,
        secure=cookie_secure(),
        samesite="lax",
        max_age=settings.refresh_token_days * 86400,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    for name, path in ((ACCESS_COOKIE, "/"), (REFRESH_COOKIE, "/api/auth"), (CSRF_COOKIE, "/")):
        response.delete_cookie(name, path=path)

"""Sentry bootstrap — API, workers (Invoice App–style options + scrubbing).

No-ops when SENTRY_DSN is empty so local/dev stays quiet.
"""

from __future__ import annotations

import re
from typing import Any

from app.core.logging import get_logger

log = get_logger("sentry")

_SECRET_KEY = re.compile(
    r"password|passwd|secret|token|authorization|cookie|api[_-]?key|private[_-]?key|session",
    re.I,
)
_LOOKS_LIKE_SECRET = re.compile(r"^(sk_|pk_|rk_|re_|whsec_|Bearer\s+|eyJ)[A-Za-z0-9._\-\/=+]{8,}$", re.I)


def _scrub_value(value: Any, depth: int = 0) -> Any:
    if depth > 4:
        return "[truncated]"
    if isinstance(value, str):
        if "@" in value and "." in value.split("@")[-1]:
            local, _, domain = value.partition("@")
            if local and domain:
                return f"*@{domain}"
        if _LOOKS_LIKE_SECRET.match(value.strip()):
            return "[redacted]"
        return value
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if _SECRET_KEY.search(str(key)):
                out[key] = "[redacted]"
            else:
                out[key] = _scrub_value(item, depth + 1)
        return out
    if isinstance(value, list):
        return [_scrub_value(item, depth + 1) for item in value[:50]]
    return value


def _before_send(event: dict, _hint: dict) -> dict | None:
    try:
        if "request" in event and isinstance(event["request"], dict):
            event["request"] = _scrub_value(event["request"])
        if "extra" in event:
            event["extra"] = _scrub_value(event["extra"])
        if "user" in event and isinstance(event["user"], dict) and "email" in event["user"]:
            event["user"]["email"] = _scrub_value(event["user"]["email"])
    except Exception:  # noqa: BLE001
        pass
    return event


def init_sentry(*, service: str = "api") -> bool:
    """Initialize Sentry if DSN configured. Returns True when armed."""
    from app.config import get_settings

    settings = get_settings()
    dsn = (settings.sentry_dsn or "").strip()
    if not dsn:
        return False
    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration

        integrations = [LoggingIntegration(level=None, event_level=None)]
        try:
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.starlette import StarletteIntegration

            if service == "api":
                integrations.extend([StarletteIntegration(), FastApiIntegration()])
        except Exception:  # noqa: BLE001
            pass
        try:
            from sentry_sdk.integrations.rq import RqIntegration

            if service in {"worker", "api"}:
                integrations.append(RqIntegration())
        except Exception:  # noqa: BLE001
            pass
        try:
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

            integrations.append(SqlalchemyIntegration())
        except Exception:  # noqa: BLE001
            pass

        traces = 0.05 if settings.is_production else 0.1
        sentry_sdk.init(
            dsn=dsn,
            environment=settings.app_env,
            traces_sample_rate=traces,
            send_default_pii=False,
            release=f"academiccheck-{service}@1.0.0",
            integrations=integrations,
            before_send=_before_send,
        )
        sentry_sdk.set_tag("service", service)
        sentry_sdk.set_tag("app", "academiccheck")
        log.info("sentry_initialized", service=service, env=settings.app_env)
        return True
    except Exception as exc:  # noqa: BLE001
        log.error("sentry_init_failed", service=service, error=str(exc))
        return False


def capture_exception(exc: BaseException, **context: object) -> None:
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_extra(key, _scrub_value(value))
            sentry_sdk.capture_exception(exc)
    except Exception:  # noqa: BLE001
        pass

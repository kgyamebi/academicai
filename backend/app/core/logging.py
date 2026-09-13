import logging
import sys

import structlog

from app.config import get_settings

_REDACT_KEYS = {
    "password",
    "password_hash",
    "token",
    "refresh_token",
    "access_token",
    "authorization",
    "secret",
    "api_key",
    "jwt",
    "cookie",
    "field_encryption_key",
}


def _redact_event(_logger: object, _method: str, event_dict: dict) -> dict:
    for key, value in list(event_dict.items()):
        lowered = str(key).lower()
        if any(part in lowered for part in _REDACT_KEYS):
            event_dict[key] = "[REDACTED]"
            continue
        if isinstance(value, str) and (
            "token=" in value.lower() or value.startswith("eyJ") or "sk_live_" in value or "sk_test_" in value
        ):
            event_dict[key] = "[REDACTED]"
    return event_dict


def configure_logging() -> None:
    settings = get_settings()
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            _redact_event,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
            if settings.is_production
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "academiccheck"):
    return structlog.get_logger(name)

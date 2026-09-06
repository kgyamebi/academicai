from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings

_PREFIX = "enc:v1:"


def _fernet() -> Fernet | None:
    settings = get_settings()
    raw = (settings.field_encryption_key or "").strip()
    if not raw:
        if settings.is_production:
            raise RuntimeError("FIELD_ENCRYPTION_KEY is required in production.")
        return None
    if raw.startswith("gAAAA"):  # already a Fernet key
        key = raw.encode()
    else:
        digest = hashlib.sha256(raw.encode()).digest()
        key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_field(value: str | None) -> str:
    if not value:
        return value or ""
    if value.startswith(_PREFIX):
        return value
    fernet = _fernet()
    if fernet is None:
        return value
    token = fernet.encrypt(value.encode("utf-8")).decode("ascii")
    return f"{_PREFIX}{token}"


def decrypt_field(value: str | None) -> str:
    if not value:
        return value or ""
    if not value.startswith(_PREFIX):
        return value
    fernet = _fernet()
    if fernet is None:
        return value
    try:
        return fernet.decrypt(value[len(_PREFIX) :].encode("ascii")).decode("utf-8")
    except InvalidToken:
        return value
